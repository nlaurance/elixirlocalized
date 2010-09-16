# -*- coding: utf-8 -*-
from elixir import has_field, Unicode, Date, using_options
from elixir import Entity
from elixirext.localized import acts_as_localized
import unittest

from elixir import setup_all, create_all, drop_all, cleanup_all

from elixir import metadata, session
from sqlalchemy.test.testing import assert_raises

from tests import engine, do_it


class Article(Entity):
    has_field('author', Unicode)
    has_field('title', Unicode)
    has_field('content', Unicode)
    has_field('release', Date)

    acts_as_localized(for_fields=['title', 'content'], default_locale='en')
    using_options(tablename='articles')


class TestLocalized(unittest.TestCase):

    def setUp(self):
        """Method used to build a database"""
        metadata.bind = engine
        setup_all()
        create_all()

        self.article = Article(author='unknown', title='A Thousand and one nights', content='It has been related to me, O happy King, said Shahrazad')
        session.add(self.article)
        session.commit()

    def tearDown(self):
        """Method used to destroy a database"""
        session.rollback()
        drop_all()

    def test_localized_versions(self):

        ar = self.article.add_locale('ar', title=u'كتاب ألف ليلة وليلة‎', content=u"قمة الأدب العربى ودرته وتاجه على مر تاريخه" )
        fr = self.article.add_locale('fr', title='Les mille et une nuits', content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade")
        assert ar in self.article.get_all_localized()
        assert fr in self.article.get_all_localized()
        assert fr.parent is self.article
        assert ar.parent is self.article

    def test_localized_code(self):

        ar = self.article.add_locale('ar', title=u'كتاب ألف ليلة وليلة‎', content=u"قمة الأدب العربى ودرته وتاجه على مر تاريخه" )
        fr = self.article.add_locale('fr', title='Les mille et une nuits', content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade")
        assert fr is self.article.get_localized('fr')
        assert ar is self.article.get_localized('ar')

    def test_not_translated(self):
        assert self.article.get_localized('bogus') is None

    def test_local_content(self):
        ar = self.article.add_locale('ar', title=u'كتاب ألف ليلة وليلة‎', content=u"قمة الأدب العربى ودرته وتاجه على مر تاريخه" )
        fr = self.article.add_locale('fr', title='Les mille et une nuits', content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade")
        # confirm local content
        assert self.article.get_localized('fr').title == 'Les mille et une nuits'
        assert self.article.get_localized('ar').title == u'كتاب ألف ليلة وليلة‎'

    def test_default_content(self):
        # default content
        assert self.article.default_locale == 'en'
        assert self.article.get_localized('en').title == self.article.title

    @do_it
    def test_get_many_localized(self):
        ar = self.article.add_locale('ar', title=u'كتاب ألف ليلة وليلة‎', content=u"قمة الأدب العربى ودرته وتاجه على مر تاريخه" )
        fr = self.article.add_locale('fr', title='Les mille et une nuits', content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade")
        session.flush()
        translations = self.article.get_many_localized(('en','fr','ar'))
        assert fr in translations
        assert ar in translations
        assert self.article in translations

    def test_not_localized_content(self):
        fr = self.article.add_locale('fr', title='Les mille et une nuits', content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade")
        # confirm non-localized content
        assert self.article.get_localized('fr').author == 'unknown'
        assert self.article.get_localized('fr').locale_id == 'fr'

    def test_python_behaviour(self):
        fr = self.article.add_locale('fr', title='Les mille et une nuits', content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade")
        fr.status = 'undergoing'
        assert fr.status == 'undergoing'
