Python API
==========

You can use Betty directly from your own Python code instead of using the :doc:`command line <cli>`:

.. code-block:: python3

    from betty.config import Configuration
    from betty.asyncio import sync
    from betty.generate import generate
    from betty.load import load
    from betty.app import App


    @sync
    async def generate():
        output_directory_path = '/var/www/betty'
        url = 'https://betty.example.com'
        configuration = Configuration(output_directory_path, url)
        async with App(configuration) as app:
            await load(app)
            await generate(app)


See the :doc:`Python module documentation <modules>` for a detailed reference of what you can do with Betty in your own
Python code.
