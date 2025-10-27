from app import app
import os

def check_ssl_certificates():
    """Verifica si existen los certificados SSL"""
    cert_path = "ssl/live/localhost/fullchain.pem"
    key_path = "ssl/live/localhost/privkey.pem"
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return (cert_path, key_path)
    return None

if __name__ == '__main__':
    ssl_context = check_ssl_certificates()
    
    if ssl_context:
        print("========================================")
        print("    F1 MANAGER - MODO HTTPS")
        print("========================================")
        print("SSL: ACTIVADO")
        print("Accede en: https://localhost:5000")
        print("Advertencia: Certificado autofirmado")
        print("========================================")
        
        app.run(
            debug=True,
            host='0.0.0.0', 
            port=5000,
            ssl_context=ssl_context
        )
    else:
        print("========================================")
        print("    F1 MANAGER - MODO HTTP")
        print("========================================")
        print("SSL: NO DISPONIBLE")
        print("Para HTTPS, ejecuta: python generate_ssl.py")
        print("Accede en: http://localhost:5000")
        print("========================================")
        
        app.run(debug=True, host='0.0.0.0', port=5000)