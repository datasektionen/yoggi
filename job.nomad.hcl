job "yoggi" {
  type = "service"

  group "yoggi" {
    network {
      port "http" {
        to = 5000
      }
    }

    service {
      name     = "yoggi"
      port     = "http"
      provider = "nomad"
      tags = [
        "traefik.enable=true",
        "traefik.http.routers.yoggi.rule=Host(`static.datasektionen.se`)",
        "traefik.http.routers.yoggi.tls.certresolver=default",
      ]
    }

    task "yoggi" {
      driver = "docker"

      config {
        image = var.image_tag
        ports = ["http"]
      }

      template {
        data        = <<ENV
{{ with nomadVar "nomad/jobs/yoggi" }}
AWS_SECRET_ACCESS_KEY={{ .aws_secret_access_key }}
LOGIN_API_KEY={{ .login_api_key }}
{{ end }}
AWS_ACCESS_KEY_ID=AKIATUCF4UAO4XR3L5W4
S3_BUCKET=dsekt-assets
LOGIN_FRONTEND_URL=https://logout.datasektionen.se/legacyapi
LOGIN_API_URL=http://logout.nomad.dsekt.internal/legacyapi
PLS_URL=http://pls.nomad.dsekt.internal
ENV
        destination = "local/.env"
        env         = true
      }

      resources {
        memory = 80
      }
    }
  }
}

variable "image_tag" {
  type = string
  default = "ghcr.io/datasektionen/yoggi:latest"
}
