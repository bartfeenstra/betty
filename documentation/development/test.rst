Testing your source code
========================

If your software project uses Betty, you may be able to use some of the many test utilities
Betty provides for your benefit:

* Pytest :py:mod:`fixtures <betty.test_utils.conftest>`
* Base classes to to help you get started writing tests for your implementations of Betty's abstract classes.
  These have class names ending in ``TestBase``.
* Dummy implementations of abstract classes. These have class names starting with ``Dummy``.
* :py:mod:`Assertion error handling <betty.test_utils.assertion>`
* Testing if your ``*.pot`` translations file is up to date with :py:class:`betty.test_utils.locale.PotFileTestBase`

All test utilities can be found in :py:mod:`betty.test_utils`.
