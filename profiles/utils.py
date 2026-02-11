import logging

logger = logging.getLogger(__name__)


def validate_phone_number(phone):
    """Validate and normalize phone number"""
    if not phone:
        return False, "Phone number is required"
    
    # Remove spaces and dashes
    phone = phone.replace(' ', '').replace('-', '')
    
    # Check if phone starts with +
    if not phone.startswith('+'):
        phone = '+' + phone
    
    # Validate digits only (after +)
    if len(phone) < 10 or len(phone) > 16:
        return False, "Phone number must be between 10-16 digits"
    
    return True, phone


def sanitize_email(email):
    """Sanitize email address"""
    if not email:
        return None
    return email.lower().strip()


def mask_phone_number(phone):
    """Mask phone number for security (show last 4 digits)"""
    if len(phone) <= 4:
        return phone
    return phone[:-4] + '****'


def validate_json_field(data, field_name, max_length=100):
    """Validate JSON field values"""
    if field_name not in data:
        return False, f"{field_name} is required"
    
    values = data[field_name]
    if not isinstance(values, list):
        return False, f"{field_name} must be a list"
    
    if not values:
        return False, f"{field_name} cannot be empty"
    
    for value in values:
        if not isinstance(value, str):
            return False, f"All {field_name} must be strings"
        
        if len(value.strip()) == 0:
            return False, f"All {field_name} must be non-empty"
        
        if len(value) > max_length:
            return False, f"Each {field_name[:-1]} must be less than {max_length} characters"
    
    return True, [v.strip() for v in values if v.strip()]