"""Test comportamentali dei tool Python di importazione.

Il test di sicurezza JavaScript (`tools/security.test.cjs`) copre il runtime
del sito, ma i tool che producono i dati sono Python. Fino a ora erano
verificati solo con un grep del loro sorgente: un controllo che passa sempre,
perche' non esegue il comportamento che dichiara di verificare. Qui si esercitano
le funzioni che difendono il filesystem e la rete.

Eseguibile senza dipendenze:  python -m unittest discover -s tools -p 'test_*.py'
"""

import json
import os
import re
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import clean_content  # noqa: E402
import download_images  # noqa: E402

PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32


class _Handler(BaseHTTPRequestHandler):
    """Server locale che serve un'immagine e un redirect verso l'esterno."""

    # Popolata da setUpClass. Va sull'attributo di classe perche' ogni richiesta
    # crea un handler nuovo: impostarla sull'istanza del server lascerebbe il
    # dizionario vuoto e ogni percorso risponderebbe con il PNG di default,
    # rendendo verdi test che dovrebbero essere rossi.
    routes = {}

    def log_message(self, *args):  # silenzia lo stderr dei test
        pass

    def do_GET(self):
        self.server.requests.append(self.path)
        route = self.routes.get(self.path)
        if route == 'redirect':
            # TLD .invalid: garantito non risolvibile (RFC 6761). Se il codice
            # seguisse il redirect otterrebbe un errore di risoluzione; se lo
            # rifiuta in base alla allow-list otterrà il ValueError atteso.
            self.send_response(302)
            self.send_header('Location', 'http://evil.invalid/lavatoio.png')
            self.end_headers()
            return
        if route == 'html':
            body = b'<html>non e\' un\'immagine</html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if route == 'notype':
            body = PNG
            self.send_response(200)
            self.send_header('Content-Type', '')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if route == 'truncated':
            # Dichiara piu' byte di quanti ne invia: e' il caso di una connessione
            # interrotta a meta' del trasferimento. Senza il controllo sul
            # Content-Length il file verrebbe pubblicato corrotto.
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(PNG) + 64))
            self.end_headers()
            self.wfile.write(PNG)
            return
        if route == 'gif89a':
            body = b'GIF89a' + b'\x00' * 32
            self.send_response(200)
            self.send_header('Content-Type', 'image/gif')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if route == 'fakewebp':
            # RIFF senza WEBP: un file solo con la firma superficiale.
            body = b'RIFF\x20\x00\x00\x00AVI LIST' + b'\x00' * 8
            self.send_response(200)
            self.send_header('Content-Type', 'image/webp')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = PNG
        self.send_response(200)
        self.send_header('Content-Type', 'image/png')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class DownloadImagesTest(unittest.TestCase):
    """Il downloader non deve mai scrivere fuori assets/img."""

    @classmethod
    def setUpClass(cls):
        _Handler.routes = {
            '/ok.png': 'png',
            '/html.png': 'html',
            '/notype.png': 'notype',
            '/redirect': 'redirect',
            '/truncated.png': 'truncated',
            '/ok.gif': 'gif89a',
            '/fake.webp': 'fakewebp',
        }
        cls.server = HTTPServer(('127.0.0.1', 0), _Handler)
        cls.server.requests = []
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _fetch(self, path):
        import ssl
        import download_images as di
        url = 'http://127.0.0.1:%d%s' % (self.port, path)
        dest = os.path.join(self.tmp(), os.path.basename(path))
        # fetch() pretende https, ma il test server e' in chiaro: si esercita la
        # logica di validazione, non il canale TLS. absolute_url viene ristretta
        # al solo loopback, cosi' l'host del test e' "consentito" e ogni altro
        # host resta rifiutato come in produzione.
        origin = 'http://127.0.0.1:%d' % self.port
        original = di.absolute_url
        di.absolute_url = lambda u, kind='link': u if u.startswith(origin) else None
        self.addCleanup(setattr, di, 'absolute_url', original)
        return di.fetch(url, dest, ssl.create_default_context())

    def tmp(self):
        import tempfile
        path = tempfile.mkdtemp(prefix='dl-test-')
        self.addCleanup(self._rmtree, path)
        return path

    @staticmethod
    def _rmtree(path):
        import shutil
        shutil.rmtree(path, ignore_errors=True)

    def test_destination_confines_traversal(self):
        """%2e%2e e varianti non possono scrivere fuori da assets/img.

        Non e' necessario che il nome venga rifiutato: e' sufficiente che il
        percorso risulti confinato nella cartella di destinazione, perche' il
        file finisca comunque dentro assets/img e non altrove.
        """
        img_dir = os.path.abspath(download_images.IMG_DIR)
        for evil in ('https://medphys.ba.infn.it/%2e%2e/%2e%2e/evil.png',
                     'https://medphys.ba.infn.it/..%2f..%2fevil.png',
                     'https://medphys.ba.infn.it/a/../../../evil.png',
                     'https://medphys.ba.infn.it/....//evil.png',
                     'https://medphys.ba.infn.it/%5C..%5Cevil.png',
                     'https://medphys.ba.infn.it/media/../../ok.png'):
            dest = download_images.destination_for(evil)
            if dest is None:
                continue  # rifiutato: outcome accettabile
            self.assertTrue(
                os.path.commonpath([os.path.abspath(dest), img_dir]) == img_dir,
                'fuori da assets/img: %s -> %s' % (evil, dest))

    def test_destination_accepts_normal(self):
        dest = download_images.destination_for(
            'https://medphys.ba.infn.it/media/ok.png')
        self.assertTrue(dest.endswith(os.path.join('img', 'ok.png')), dest)

    def test_absolute_url_blocks_other_hosts(self):
        for bad in ('http://medphys.ba.infn.it/a.png',      # http
                    'https://evil.tld/medphys.ba.infn.it/a.png',  # sottostringa
                    'https://medphys.ba.infn.it.evil.tld/a.png',  # suffisso
                    'https://medphys.ba.infn.it@evil.tld/a.png'):  # userinfo
            self.assertIsNone(download_images.absolute_url(bad), bad)

    def test_protocol_relative_is_upgraded_to_https(self):
        """//host non viene rifiutato ma forzato su https, con host verificato."""
        self.assertEqual(
            download_images.absolute_url('//medphys.ba.infn.it/a.png'),
            'https://medphys.ba.infn.it/a.png')
        self.assertIsNone(download_images.absolute_url('//evil.tld/a.png'))

    def test_absolute_url_rejects_credentials(self):
        self.assertIsNone(download_images.absolute_url(
            'https://user:pw@medphys.ba.infn.it/a.png'))

    def test_fetch_rejects_redirect_off_allowlist(self):
        """Un 302 verso un host non consentito deve fallire, non seguire."""
        with self.assertRaises(Exception) as ctx:
            self._fetch('/redirect')
        self.assertIn('redirect', str(ctx.exception).lower())

    def test_fetch_rejects_html_content_type(self):
        """HTML servito come .png non deve finire su disco."""
        with self.assertRaises(ValueError):
            self._fetch('/html.png')

    def test_fetch_rejects_missing_content_type(self):
        """Content-Type assente non e' un pass."""
        with self.assertRaises(ValueError):
            self._fetch('/notype.png')

    def test_fetch_rejects_content_not_matching_extension(self):
        """Un .png che non inizia con la firma PNG viene rifiutato."""
        import ssl
        import download_images as di
        url = 'http://127.0.0.1:%d/ok.png' % self.port
        dest = os.path.join(self.tmp(), 'ok.png')
        original = di.MAGIC
        di.MAGIC = {'.png': b'NON-E-UNA-IMMAGINE'}
        try:
            with self.assertRaises(ValueError):
                di.fetch(url, dest, ssl.create_default_context())
        finally:
            di.MAGIC = original
        self.assertFalse(os.path.exists(dest), 'file scritto nonostante il rifiuto')

    def test_fetch_writes_atomically(self):
        """Il file finale compare solo a download completo, e senza .part."""
        import ssl
        import download_images as di
        target = os.path.join(self.tmp(), 'ok.png')
        di.fetch('http://127.0.0.1:%d/ok.png' % self.port, target,
                 ssl.create_default_context())
        self.assertTrue(os.path.exists(target))
        self.assertFalse(os.path.exists(target + '.part'), 'resta il file .part')
        with open(target, 'rb') as handle:
            self.assertTrue(handle.read().startswith(PNG[:8]))

    def test_fetch_rejects_truncated_body(self):
        """Una risposta incompleta non deve diventare un file pubblicato."""
        import ssl
        import download_images as di
        target = os.path.join(self.tmp(), 'truncated.png')
        with self.assertRaises(ValueError):
            di.fetch('http://127.0.0.1:%d/truncated.png' % self.port, target,
                     ssl.create_default_context())
        self.assertFalse(os.path.exists(target), 'file scritto nonostante il troncamento')
        self.assertFalse(os.path.exists(target + '.part'), 'resta il file .part')

    def test_gif89a_is_accepted(self):
        """GIF89a e' una GIF valida: la firma corretta e' GIF8, non GIF87a."""
        import ssl
        import download_images as di
        target = os.path.join(self.tmp(), 'ok.gif')
        di.fetch('http://127.0.0.1:%d/ok.gif' % self.port, target,
                 ssl.create_default_context())
        with open(target, 'rb') as handle:
            self.assertTrue(handle.read().startswith(b'GIF89a'))

    def test_webp_must_carry_the_webp_signature(self):
        """Un file RIFF che non contiene WEBP non e' un'immagine WebP."""
        import ssl
        import download_images as di
        target = os.path.join(self.tmp(), 'fake.webp')
        with self.assertRaises(ValueError):
            di.fetch('http://127.0.0.1:%d/fake.webp' % self.port, target,
                     ssl.create_default_context())
        self.assertFalse(os.path.exists(target), 'file scritto nonostante il rifiuto')

    def test_failed_download_leaves_nothing_behind(self):
        """Dopo un fallimento non deve restare un .part nel filesystem."""
        import ssl
        import download_images as di
        target = os.path.join(self.tmp(), 'html.png')
        with self.assertRaises(ValueError):
            di.fetch('http://127.0.0.1:%d/html.png' % self.port, target,
                     ssl.create_default_context())
        leftovers = os.listdir(os.path.dirname(target))
        self.assertEqual(leftovers, [], 'residui: %s' % leftovers)

def test_main_reports_failure(self):
        """Un download fallito deve far fallire main(), non essere nascosto.

        Il manifesto registra solo i file scaricati: senza questo controllo un
        import andato a meta' terminava con successo e la CI restava verde
        mentre assets/img era incompleto.
        """
        import download_images as di
        work = self.tmp()
        original = (di.IMG_DIR, di.TMP, di.collect_urls)
        di.IMG_DIR = os.path.join(work, 'img')
        di.TMP = os.path.join(work, 'tmp')
        di.collect_urls = lambda: ['http://127.0.0.1:%d/html.png' % self.port]

        def restore():
            di.IMG_DIR, di.TMP, di.collect_urls = original

        self.addCleanup(restore)
        # La risposta e' text/html: fetch la rifiuta, quindi fallisce.
        self.assertNotEqual(di.main(), 0, 'main() ha restituito successo')



class CleanContentTest(unittest.TestCase):
    """Il generatore non deve perdere contenuto che il runtime mostrerebbe."""

    def test_inline_spaces_are_preserved(self):
        """Uno spazio fra due elementi inline e' contenuto, non impaginazione."""
        out = clean_content.clean('<p>Parola <b>grasso</b> <b>altro</b></p>')
        self.assertIn('<b>grasso</b> <b>altro</b>', out, out)

    def test_newline_between_tags_is_collapsed(self):
        out = clean_content.clean('<p>uno</p>\n    <p>due</p>')
        self.assertIn('<p>uno</p><p>due</p>', out, out)

    def test_alt_is_not_double_encoded(self):
        out = clean_content.clean(
            '<img src="assets/img/a.png" alt="A &amp; B">')
        self.assertIn('alt="A &amp; B"', out, out)
        self.assertNotIn('&amp;amp;', out, out)

    def test_video_wrapper_class_survives(self):
        """La classe usata dal CSS non deve sparire alla rigenerazione."""
        out = clean_content.clean('<div class="video-embed">V</div>')
        self.assertIn('class="video-embed"', out, out)

    def test_external_link_keeps_target(self):
        out = clean_content.clean(
            '<a href="https://example.org/x" target="_blank">L</a>')
        self.assertIn('target="_blank"', out, out)
        self.assertIn('rel="noopener noreferrer"', out, out)

    def test_hostile_target_is_dropped(self):
        """Un target arbitrario viene rimosso, non propagato ne' sostituito.

        Sostituirlo con _blank cambierebbe il comportamento del link senza
        che nulla lo richieda: il valore scartato non viene re-inventato.
        """
        out = clean_content.clean(
            '<a href="https://example.org/x" target="evilframe">L</a>')
        self.assertNotIn('evilframe', out, out)
        self.assertNotIn('target=', out, out)
        self.assertIn('href="https://example.org/x"', out, out)

    def test_target_is_not_invented(self):
        """Senza target nel sorgente il generatore non ne aggiunge uno.

        Il dato pubblicato non usa target="_blank": rigenerare non deve
        cambiare il modo in cui si aprono i link per i visitatori.
        """
        out = clean_content.clean('<a href="https://example.org/x">L</a>')
        self.assertNotIn('target=', out, out)

    def test_mailto_does_not_open_a_new_tab(self):
        """mailto: e tel: restano senza target: aprirebbero una scheda vuota."""
        for url in ('mailto:a@b.example', 'tel:+3901234567'):
            out = clean_content.clean('<a href="%s">X</a>' % url)
            self.assertNotIn('target=', out, out)
            self.assertIn('href="%s"' % url, out, out)

    def test_hostile_mailto_is_rejected(self):
        """Anche mailto: passa dalla validazione: non e' un'eccezione.

        Accettare mailto senza controllo lascerebbe passare backslash e
        caratteri di controllo, che sono esattamente cio' che safe_url blocca
        per gli altri schemi.
        """
        for url in ('mailto:a@b.example\\evil', 'mailto:a@b.example\nX'):
            out = clean_content.clean('<p><a href="%s">X</a></p>' % url)
            # Il collegamento rifiutato non deve lasciare un <a> vuoto: il testo
            # resta, il tag sparisce come per qualsiasi altro href non ammesso.
            self.assertNotIn('<a', out, url)
            self.assertNotIn('href=', out, url)
            self.assertIn('X', out, url)

    def test_http_link_is_rejected_and_counted(self):
        """http: non e' ammesso dal runtime: il testo resta, il link no.

        Il conteggio serve a rendere la perdita visibile invece di lasciare
        che emerga solo a runtime.
        """
        clean_content.REJECTED_LINKS.clear()
        out = clean_content.clean('<p><a href="http://insecure.example/x">X</a></p>')
        self.assertNotIn('<a ', out, out)
        self.assertIn('X', out, out)
        self.assertEqual(clean_content.REJECTED_LINKS.get('http:'), 1,
                         clean_content.REJECTED_LINKS)

    def test_backslash_url_is_rejected(self):
        """Il browser risolve il backslash come '/': cambia l'origin."""
        self.assertIsNone(clean_content.safe_url('https:\\evil.example/x', 'link'))
        self.assertIsNone(clean_content.safe_url('\\evil.example', 'link'))
        self.assertEqual(clean_content.safe_url('https://ok.example/a', 'link'),
                         'https://ok.example/a')

    def test_void_tag_in_drop_subtree_does_not_swallow_the_page(self):
        """Un tag void non ha chiusura: cercarla consumerebbe tutto il resto.

        `source`, `track`, `meta` e `link` sono void e vengono scartati: se il
        rimborso non li tratta come markup singolo, sparisce anche la pagina.
        """
        for tag in ('<link rel="stylesheet" href="x.css">',
                    '<meta name="x" content="y">',
                    '<source src="x.mp4">',
                    '<track src="t.vtt">'):
            out = clean_content.clean('<p>a</p>' + tag + '<p>b</p>')
            self.assertIn('<p>a</p>', out, tag)
            self.assertIn('<p>b</p>', out, tag)

    def test_allowed_void_tags_survive(self):
        """img, br e hr sono void ma ammessi: non vanno rimossi insieme agli altri."""
        out = clean_content.clean('<p>a</p><img src="assets/img/a.png" alt="A">'
                                  '<br><hr><p>b</p>')
        self.assertIn('<img src="assets/img/a.png"', out, out)
        self.assertIn('<br>', out, out)
        self.assertIn('<hr>', out, out)

    def test_image_title_survives(self):
        """Il runtime ammette title sulle immagini: non deve andare perso."""
        out = clean_content.clean(
            '<img src="assets/img/a.png" alt="A" title="Didascalia">')
        self.assertIn('title="Didascalia"', out, out)

    def test_greater_than_inside_attribute_does_not_corrupt_markup(self):
        """Un '>' dentro href o title non deve troncare il tag.

        Cercando il primo '>' il resto dell'attributo finirebbe nel testo del
        link, producendo markup malformato.
        """
        out = clean_content.clean(
            '<a href="https://ok.example/x?a=1>2" title="t>u">L</a>')
        self.assertIn('href="https://ok.example/x?a=1&gt;2"', out, out)
        self.assertIn('title="t&gt;u"', out, out)
        self.assertTrue(out.endswith('>L</a>'), out)
        self.assertNotIn('?a=1>2"', out, out)

    def test_title_survives_on_internal_link(self):
        """Il titolo va conservato anche sui link che diventano #/slug."""
        out = clean_content.clean(
            '<a href="https://medphys.ba.infn.it/people/" title="Persone">P</a>')
        self.assertIn('href="#/people"', out, out)
        self.assertIn('title="Persone"', out, out)

    def test_title_survives_on_anchor_link(self):
        out = clean_content.clean('<a href="#/brain" title="Cervello">B</a>')
        self.assertIn('title="Cervello"', out, out)

    def test_ampersand_in_href_is_escaped(self):
        """Una & nuda in un attributo non e' HTML valido."""
        out = clean_content.clean(
            '<a href="https://ok.example/s?a=1&b=2">L</a>')
        self.assertIn('a=1&amp;b=2', out, out)

    def test_heading_keeps_no_id_nor_class(self):
        """Il runtime non accetta id/class sui heading: non vanno emessi."""
        out = clean_content.clean('<h2 id="x" class="y">T</h2>')
        self.assertEqual(out, '<h2>T</h2>', out)

    def test_bom_does_not_survive_as_page_content(self):
        """Senza utf-8-sig il BOM diventerebbe il contenuto della pagina.

        Una pagina senza corpo deve restare stringa vuota, non '\\ufeff'.
        """
        import tempfile
        root = tempfile.mkdtemp(prefix='bom-')
        with open(os.path.join(root, 'x.html'), 'w', encoding='utf-8-sig') as handle:
            handle.write('<!-- TITLE: T --> <!-- SLUG: x --> <!-- LINK: /x/ --> \ufeff\n')
        original_ex = clean_content.EX
        clean_content.EX = root
        self.addCleanup(setattr, clean_content, 'EX', original_ex)
        body = clean_content.read_meta('x.html')
        self.assertEqual(body[3], '', repr(body[3]))

    def test_main_fails_without_extraction(self):
        """Senza estrazione main() deve fermarsi, non uscire con successo."""
        import tempfile
        original_ex, original_out = clean_content.EX, clean_content.OUT
        clean_content.EX = os.path.join(tempfile.mkdtemp(prefix='vuoto-'), 'extract')
        clean_content.OUT = tempfile.mkdtemp(prefix='out-')

        def restore():
            clean_content.EX, clean_content.OUT = original_ex, original_out

        self.addCleanup(restore)
        with self.assertRaises(SystemExit):
            clean_content.main()

    def test_active_markup_is_dropped(self):
        for evil in ('<script>alert(1)</script>', '<style>x{}</style>',
                     '<form action="/x">y</form>', '<svg onload="alert(1)"></svg>'):
            out = clean_content.clean('<p>a</p>' + evil)
            self.assertNotIn('<script', out)
            self.assertNotIn('<style', out)
            self.assertNotIn('<form', out)
            self.assertNotIn('<svg', out)

    def test_unknown_tag_loses_markup_but_keeps_text(self):
        out = clean_content.clean('<marquee>testo</marquee>')
        self.assertNotIn('<marquee', out)
        self.assertIn('testo', out)

    def test_javascript_href_is_neutralised(self):
        out = clean_content.clean(
            '<a href="javascript:alert(1)">clic</a>')
        self.assertNotIn('javascript:', out)

    def test_object_inherited_keys_are_not_tags(self):
        """<toString> non deve far scartare tutto il contenuto seguente."""
        out = clean_content.clean('<p>prima</p><toString>mezzo</toString><p>dopo</p>')
        self.assertIn('prima', out)
        self.assertIn('mezzo', out)
        self.assertIn('dopo', out)


class AllowListSyncTest(unittest.TestCase):
    """Le allow-list del generatore e del runtime devono restare allineate."""

    def test_generator_allowlist_matches_runtime(self):
        path = os.path.join(os.path.dirname(download_images.__file__),
                            '..', 'assets', 'js', 'sanitize.js')
        with open(path, encoding='utf-8') as handle:
            source = handle.read()

        runtime_tags = _parse_js_set(source, 'ALLOWED_TAGS')
        self.assertTrue(runtime_tags, 'ALLOWED_TAGS non trovato in sanitize.js')
        self.assertEqual(
            sorted(clean_content.ALLOWED_TAGS),
            sorted(runtime_tags),
            'ALLOWED_TAGS divergente fra clean_content.py e sanitize.js')

        runtime_drop = _parse_js_set(source, 'DROP_SUBTREE_TAGS')
        self.assertTrue(runtime_drop, 'DROP_SUBTREE_TAGS non trovato in sanitize.js')
        self.assertEqual(
            sorted(clean_content.DROP_SUBTREE_TAGS),
            sorted(runtime_drop),
            'DROP_SUBTREE_TAGS divergente fra clean_content.py e sanitize.js')

    def test_generator_classes_match_runtime(self):
        path = os.path.join(os.path.dirname(download_images.__file__),
                            '..', 'assets', 'js', 'sanitize.js')
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
        runtime_classes = set(re.findall(r"'([a-z0-9-]+)':\s*1", _slice(source, 'ALLOWED_CLASSES')))
        self.assertEqual(
            sorted(clean_content.ALLOWED_CLASSES),
            sorted(runtime_classes),
            'ALLOWED_CLASSES divergente fra clean_content.py e sanitize.js')


def _slice(source, name):
    start = source.index('var ' + name)
    end = source.index('};', start)
    return source[start:end]


def _parse_js_set(source, name):
    block = _slice(source, name)
    return set(re.findall(r"([A-Za-z][\w-]*)\s*:", block))


class SourceDataTest(unittest.TestCase):
    """I JSON sorgenti dei generatori devono essere utilizzabili."""

    def _load(self, name):
        path = os.path.join(os.path.dirname(download_images.__file__), '..',
                            'assets', 'data', name)
        with open(path, encoding='utf-8') as handle:
            raw = handle.read()
        # Un marcatore di conflitto Git renderebbe il file non parsabile: si
        # controlla prima di json.load, altrimenti l'errore sarebbe generico.
        for marker in ('<<<<<<<', '=======', '>>>>>>>'):
            self.assertNotIn(marker, raw,
                             '%s contiene il marcatore di conflitto %r' % (name, marker))
        return json.loads(raw)

    def test_pages_en_json_is_valid(self):
        """pages_en.json e' la sorgente di gen_en.py: se e' rotto, il tool muore."""
        pages = self._load('pages_en.json')
        self.assertIsInstance(pages, dict)
        self.assertGreater(len(pages), 0)

    def test_meta_json_is_valid(self):
        meta = self._load('meta.json')
        self.assertIsInstance(meta, dict)
        self.assertGreater(len(meta), 0)

    def test_source_json_covers_every_published_page(self):
        """Ogni pagina servita deve avere una voce nella sua sorgente."""
        pages = self._load('pages_en.json')
        path = os.path.join(os.path.dirname(download_images.__file__), '..',
                            'assets', 'data', 'pages_en.js')
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
        published = json.loads(
            source[source.index('=') + 1:
                   source.index(';\nwindow.MEDPHYS_META')].strip())
        self.assertEqual(sorted(pages), sorted(published),
                         'pages_en.json e pages_en.js non hanno gli stessi slug')


if __name__ == '__main__':
    unittest.main()
