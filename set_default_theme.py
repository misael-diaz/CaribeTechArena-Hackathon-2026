import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Byte.settings')
django.setup()

from admin_interface.models import Theme

def create_biofood_theme():
    Theme.objects.all().delete()
    
    theme = Theme.objects.create(
        name='BioFood Premium',
        active=True,
        title='BioFood Admin',
        title_visible=True,
        logo_visible=True,
        css_header_background_color='#27ae60',
        css_header_text_color='#ffffff',
        css_header_link_color='#ffffff',
        css_header_link_hover_color='#f1c40f',
        css_module_background_color='#2ecc71',
        css_module_text_color='#ffffff',
        css_module_link_color='#ffffff',
        css_module_link_hover_color='#f1c40f',
        css_generic_link_color='#27ae60',
        css_generic_link_hover_color='#2ecc71',
        css_save_button_background_color='#27ae60',
        css_save_button_background_hover_color='#2ecc71',
        css_save_button_text_color='#ffffff',
        css_delete_button_background_color='#e74c3c',
        css_delete_button_background_hover_color='#c0392b',
        css_delete_button_text_color='#ffffff',
        list_filter_dropdown=True,
        related_modal_active=True,
        related_modal_background_color='#000000',
        related_modal_background_opacity='0.3',
        related_modal_rounded_corners=True,
        related_modal_close_button_visible=True,
    )
    print(f"Theme '{theme.name}' created and activated!")

if __name__ == "__main__":
    create_biofood_theme()
