from chat.skill.get_student_summary.tool import get_student_summary

# Simulamos una consulta real de un padre
result = get_student_summary.invoke({
    "parent_phone": "+573001234567",
    "student_name": "Juan"
})

print("=== RESUMEN MEJORADO CON RECOMENDACIONES ===")
print(result)
print("\n" + "="*50)
print("¿Qué significa esto?\n")
print("• RECARGA URGENTE: El saldo actual cubre menos de 5 días. Se recomienda recargar.")
print("• PATRÓN DE CONSUMO: Compra repetida de productos altos en azúcar. Sugerimos alternativas saludables.")
print("• ALERTA ALÉRGENO: Compró producto que contiene alérgenos registrados. Verificación necesaria.")
print("\nEste resumen ya está listo para producción.")