variable "app_version" {
  description = "Version de la aplicacion BancoNova"
  type        = string
  default     = "1.0.0"
}
variable "kube_config_path" {
  description = "Ruta al archivo kubeconfig"
  type        = string
  default     = "~/.kube/config"
}
variable "kube_context" {
  description = "Contexto de Kubernetes (minikube para local)"
  type        = string
  default     = "minikube"
}
variable "imagen_docker" {
  description = "Nombre de la imagen Docker de BancoNova"
  type        = string
  default     = "banconova-app"
}
variable "replicas_desarrollo" {
  description = "Replicas en desarrollo"
  type        = number
  default     = 1
}
variable "replicas_produccion" {
  description = "Replicas en produccion"
  type        = number
  default     = 2
}
variable "puerto_desarrollo" {
  description = "NodePort del ambiente de desarrollo"
  type        = number
  default     = 30001
}
variable "puerto_produccion" {
  description = "NodePort del ambiente de produccion"
  type        = number
  default     = 30002
}
