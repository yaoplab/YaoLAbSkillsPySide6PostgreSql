from larccommon.l10n import Translator, _

class TestL10n:
    def test_translator_init(self):
        tr = Translator("fr")
        assert tr.lang == "fr"

    def test_translator_set_lang(self):
        tr = Translator("fr")
        tr.set_language("en")
        assert tr.lang == "en"

    def test_translator_load(self):
        tr = Translator("fr")
        tr.load("C:/projets/LarcCommon/larccommon/l10n/fr.json")
        assert tr.t("common.button.save") == "Enregistrer"

    def test_translator_missing_key(self):
        tr = Translator("fr")
        assert tr.t("nonexistent.key") == "nonexistent.key"

    def test_translator_default(self):
        tr = Translator("fr")
        assert tr.t("nonexistent", "default_val") == "default_val"

    def test_translator_load_dir(self):
        tr = Translator("fr")
        tr.load_dir("C:/projets/LarcCommon/larccommon/l10n")
        assert tr.t("common.button.cancel") == "Annuler"

    def test_translator_reload(self):
        tr = Translator("fr")
        tr.load_dir("C:/projets/LarcCommon/larccommon/l10n")
        tr.reload("C:/projets/LarcCommon/larccommon/l10n")
        assert tr.t("common.button.save") == "Enregistrer"

    def test_en_translation(self):
        tr = Translator("en")
        tr.load_dir("C:/projets/LarcCommon/larccommon/l10n")
        assert tr.t("common.button.save") == "Save"

    def test_underscore_function(self):
        tr = Translator("fr")
        tr.load_dir("C:/projets/LarcCommon/larccommon/l10n")
        from larccommon.l10n import _
        # _ is a reference to Translator.instance().t, needs locale setup
        tr2 = Translator.instance("fr")
        tr2.load_dir("C:/projets/LarcCommon/larccommon/l10n")
        assert _("common.button.save") == "Enregistrer"

    def test_load_multiple(self):
        tr = Translator("fr")
        tr.load("C:/projets/LarcCommon/larccommon/l10n/fr.json")
        assert tr.t("common.button.save") == "Enregistrer"
        assert tr.t("common.button.cancel") == "Annuler"
