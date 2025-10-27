from app import app

if __name__ == '__main__':
    print("Iniciando servidor F1 Manager...")
    print("La aplicación estará disponible en: http://localhost:5000")
    print("Presiona Ctrl+C para detener el servidor")
    app.run(debug=True)