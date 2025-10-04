import os
import uuid
import magic
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_MIME_TYPES = {
    'image/png',
    'image/jpeg',
    'image/jpg'
}

MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_file_extension(filename):
    """التحقق من امتداد الملف"""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS

def validate_mime_type(file_path):
    """التحقق من نوع MIME الفعلي للملف"""
    try:
        mime = magic.Magic(mime=True)
        file_mime = mime.from_file(file_path)
        return file_mime in ALLOWED_MIME_TYPES
    except Exception as e:
        current_app.logger.error(f'خطأ في التحقق من MIME: {str(e)}')
        return False

def validate_file_size(file):
    """التحقق من حجم الملف"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size <= MAX_FILE_SIZE

def generate_secure_filename(original_filename):
    """توليد اسم ملف آمن وعشوائي"""
    if not original_filename or '.' not in original_filename:
        raise ValueError('اسم ملف غير صالح')
    
    ext = original_filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f'امتداد الملف غير مسموح. الامتدادات المسموحة: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}')
    
    random_name = str(uuid.uuid4())
    safe_filename = f"{random_name}.{ext}"
    return secure_filename(safe_filename)

def validate_payment_data(data):
    """التحقق القوي من بيانات الدفع"""
    errors = []
    
    required_fields = {
        'method_id': 'معرف طريقة الدفع',
        'sender_name': 'اسم المُرسل',
        'sender_phone': 'رقم الهاتف',
        'amount': 'المبلغ',
        'payment_date': 'تاريخ الدفع'
    }
    
    for field, label in required_fields.items():
        if field not in data or not data[field]:
            errors.append(f'{label} مطلوب')
    
    if 'sender_name' in data:
        name = str(data['sender_name']).strip()
        if len(name) < 3:
            errors.append('اسم المُرسل يجب أن يكون 3 أحرف على الأقل')
        if len(name) > 255:
            errors.append('اسم المُرسل طويل جداً (الحد الأقصى 255 حرف)')
    
    if 'sender_phone' in data:
        phone = str(data['sender_phone']).strip()
        if len(phone) < 9:
            errors.append('رقم الهاتف غير صالح (9 أرقام على الأقل)')
        if len(phone) > 15:
            errors.append('رقم الهاتف طويل جداً (الحد الأقصى 15 رقم)')
        if not phone.replace('+', '').replace(' ', '').isdigit():
            errors.append('رقم الهاتف يجب أن يحتوي على أرقام فقط')
    
    if 'amount' in data:
        try:
            amount = float(data['amount'])
            if amount <= 0:
                errors.append('المبلغ يجب أن يكون أكبر من صفر')
            if amount > 10000000:
                errors.append('المبلغ كبير جداً')
        except (ValueError, TypeError):
            errors.append('المبلغ غير صالح')
    
    if 'transaction_reference' in data and data['transaction_reference']:
        ref = str(data['transaction_reference']).strip()
        if len(ref) > 255:
            errors.append('مرجع العملية طويل جداً (الحد الأقصى 255 حرف)')
    
    return errors

def sanitize_filename(filename):
    """تنظيف اسم الملف من المحارف الخطرة"""
    if not filename:
        return None
    
    filename = filename.strip()
    dangerous_chars = ['..', '/', '\\', '\0', '\n', '\r', '\t']
    
    for char in dangerous_chars:
        filename = filename.replace(char, '')
    
    return secure_filename(filename)

def validate_and_save_file(file, upload_folder):
    """
    التحقق الشامل من الملف وحفظه بشكل آمن
    
    Returns:
        tuple: (success: bool, result: str or dict)
    """
    if not file or file.filename == '':
        return False, {'error': 'لم يتم اختيار ملف'}
    
    if not validate_file_extension(file.filename):
        return False, {'error': f'نوع الملف غير مسموح. الامتدادات المسموحة: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'}
    
    if not validate_file_size(file):
        return False, {'error': f'حجم الملف يجب أن يكون أقل من {MAX_FILE_SIZE / (1024*1024):.0f} ميجابايت'}
    
    try:
        safe_filename = generate_secure_filename(file.filename)
        
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, safe_filename)
        file.save(file_path)
        
        if not validate_mime_type(file_path):
            os.remove(file_path)
            return False, {'error': 'نوع الملف غير صالح. يجب أن يكون صورة PNG أو JPEG فقط'}
        
        return True, {'filename': safe_filename, 'path': file_path}
        
    except Exception as e:
        current_app.logger.error(f'خطأ في حفظ الملف: {str(e)}')
        return False, {'error': f'فشل في حفظ الملف: {str(e)}'}
