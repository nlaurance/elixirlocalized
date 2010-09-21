Localized Elixir Statement Generator

by Isaac Csandl, borrowing a bit from Jonathan LaCour's acts_as_versioned.
modified by Graham Higgins
rewritten for elixir 0.7 by Nicolas Laurance with contibutions of Yannick Bréhon.

=========
Localized
=========

About Localized database conent
-------------------------------

This allows you to localize the data contained in your Elixir entities.

.. notes:

    You are on your own to use standard locale strings such as 'en', 'es', etc.

Example usage::

    >>> from elixir import *
    >>> from elixirext.localized import acts_as_localized

    >>> class Article(Entity):
    ...     has_field('author', Unicode)
    ...     has_field('title', Unicode)
    ...     has_field('content', Unicode)
    ...     has_field('release', Date)
    ...     acts_as_localized(for_fields=['title', 'content'], default_locale='en')
    ...     using_options(tablename='articles')
    ...

    setup the environment

    >>> engine = 'sqlite:///:memory:'
    >>> metadata.bind = engine
    >>> setup_all()
    >>> create_all()

    Let's create an article in the default language

    >>> article = Article(author='unknown', title='A Thousand and one nights', content='It has been related to me, O happy King, said Shahrazad')

    We translate it in french

    >>> fr = article.add_locale('fr', title='Les mille et une nuits', content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade")
    >>> session.flush()
    >>> session.expunge()

    We can then access the translated attributes

    >>> article = Article.get(1)
    >>> article.get_localized('fr').title
    'Les mille et une nuits'

    Other attributes are left untouched

    >>> article.get_localized('fr').author
    'unknown'



Statement Options
-----------------

This Elixir Statement has two options:

+--------------------+----------------------------------------------------+
| Option Name        | Description                                        |
+====================+====================================================+
| ``for_fields``     | List of field names to localize.                   |
+--------------------+----------------------------------------------------+
| ``default_locale`` | A locale identifier such as 'en', 'fr', 'de', etc. |
|                    | Defaults to 'en'.                                  |
+--------------------+----------------------------------------------------+

The Statement adds three methods to your Entity:

`get_localized(locale_string)`
------------------------------

returns the localized object for the locale_string or None

`get_all_localized`
-------------------

This is a list of all localized versions, or [] if none.

`add_locale(locale_string, [keyword arguments])`
------------------------------------------------

Creates and returns a new localized object for the locale_string. You can add on
any keyword arguments to automatically initialize the localized fields.
