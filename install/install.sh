#!/bin/bash

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
  -h | --help)
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message and exit"
    echo "  --ip IP         IP address to bind the app to"
    echo "  --port PORT     Port to bind the app to"
    echo "  --wg WG         Path to wg"
    echo "  --tls-cert      Path to TLS certificate file"
    echo "  --tls-key       Path to TLS key file"
    exit 0
    ;;
  --ip)
    IP="$2"
    shift # past argument
    shift # past value
    ;;
  --port)
    PORT="$2"
    shift # past argument
    shift # past value
    ;;
  --wg)
    WG="$2"
    shift # past argument
    shift # past value
    ;;
  --tls-cert)
    TLS_CERT="$2"
    shift # past argument
    shift # past value
    ;;
  --tls-key)
    TLS_KEY="$2"
    shift # past argument
    shift # past value
    ;;
  *)      # unknown option
    shift # past argument
    ;;
  esac
done

# Install necessary packages
pip3 install -r /opt/wireguard-exporter/install/requirements.txt

# Create the service file
sudo tee /etc/systemd/system/wireguard-exporter.service <<EOF
[Unit]
Description=Wireguard Metrics Exporter for Prometheus
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/wireguard-exporter
EOF

# Add optional parameters to the service file if specified
if [ -n "$TLS_CERT" ] && [ -n "$TLS_KEY" ]; then
  echo "ExecStart=/usr/bin/env python3 /opt/wireguard-exporter/src/main.py --tls-cert $TLS_CERT --tls-key $TLS_KEY" | sudo tee -a /etc/systemd/system/wireguard-exporter.service >/dev/null
else
  echo "ExecStart=/usr/bin/env python3 /opt/wireguard-exporter/src/main.py" | sudo tee -a /etc/systemd/system/wireguard-exporter.service >/dev/null
fi

# Add the remaining lines of the service file
sudo tee -a /etc/systemd/system/wireguard-exporter.service <<EOF
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload the systemd daemon
sudo systemctl daemon-reload

# Start the service and enable it on boot
sudo systemctl start wireguard-exporter
sudo systemctl enable wireguard-exporter

# Check status of service
sudo systemctl status wireguard-exporter
