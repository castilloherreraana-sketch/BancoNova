output "namespace_desarrollo" {
  description = "Namespace de desarrollo creado"
  value       = kubernetes_namespace.desarrollo.metadata[0].name
}
output "namespace_produccion" {
  description = "Namespace de produccion creado"
  value       = kubernetes_namespace.produccion.metadata[0].name
}
output "url_desarrollo" {
  description = "URL del ambiente de desarrollo"
  value       = "http://localhost:${var.puerto_desarrollo}"
}
output "url_produccion" {
  description = "URL del ambiente de produccion"
  value       = "http://localhost:${var.puerto_produccion}"
}
