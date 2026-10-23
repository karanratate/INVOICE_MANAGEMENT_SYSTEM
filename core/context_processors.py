from django.conf import settings

def company_settings(request):
    return {
        'company_name': settings.COMPANY_NAME,
        'company_address': settings.COMPANY_ADDRESS,
        'company_city': settings.COMPANY_CITY,
        'company_state': settings.COMPANY_STATE,
        'company_zip': settings.COMPANY_ZIP,
        'company_country': settings.COMPANY_COUNTRY,
        'company_phone': settings.COMPANY_PHONE,
        'company_email': settings.COMPANY_EMAIL,
        'company_logo': settings.COMPANY_LOGO,
        'invoice_prefix': settings.INVOICE_PREFIX,
        'currency': settings.CURRENCY,
        'currency_symbol': settings.CURRENCY_SYMBOL,
        'vat_rate': settings.VAT_RATE,
        'enable_vat': settings.ENABLE_VAT,
    }