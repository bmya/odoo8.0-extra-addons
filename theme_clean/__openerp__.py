{
    'name': 'Clean Theme',
    'description': 'Clean Theme',
    'image': 'Clean_description.jpg',
    'category': 'Theme',
    'version': '1.0',
    'author': 'Odoo SA',
    'depends': ['theme_common'],
    'data': [
        'views/assets.xml',
        'views/customize_modal.xml',
        'views/image_content.xml',
        'views/image_library.xml',
        'views/snippets_options.xml',
        'views/snippets.xml',
    ],
    'demo': [
        'demo/home.xml',
        'demo/blocks.xml',
    ],
    'application': True,
}
