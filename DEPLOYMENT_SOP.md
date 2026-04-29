# FastShop: Complete Deployment SOP

## Table of Contents
1. [Git Repository Setup & GitHub Push](#1-git-repository-setup--github-push)
2. [Azure Server Setup](#2-azure-server-setup)
3. [Running & Accessing the Application](#3-running--accessing-the-application)

---

## 1. Git Repository Setup & GitHub Push

### Prerequisites
- Git installed on local machine (`git --version`)
- GitHub account created
- SSH key configured (or HTTPS token)

### Step-by-Step Instructions

#### Step 1.1: Initialize Local Git Repository
```bash
# Navigate to FastShop directory
cd C:\Users\akash\FastShop

# Initialize git repository
git init

# Configure git user (one-time)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# View git status
git status
```

#### Step 1.2: Create `.gitignore` File (Root Level)
```bash
# Create root-level .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log
yarn-error.log
dist/

# Databases
*.db
*.db-journal

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.*.local
EOF
```

#### Step 1.3: Stage and Commit All Files
```bash
# Add all files to staging area
git add .

# Create initial commit
git commit -m "Initial commit: FastShop microservices e-commerce platform

- Phase 1: Docker Compose orchestration and comprehensive README
- Phase 2: Identity Hub (JWT authentication)
- Phase 3: Product Hub (catalog management)
- Phase 4: Transaction Hub (cart & checkout with stock verification)
- Phase 5: Frontend App (React + Vite + TailwindCSS)
"

# View commit log
git log
```

#### Step 1.4: Create GitHub Repository
- Go to https://github.com/new
- **Repository name**: `FastShop`
- **Description**: "Lightweight microservices e-commerce platform optimized for 6GB RAM systems"
- **Visibility**: Public (or Private if preferred)
- **Initialize**: Do NOT check "Add README" (we already have one)
- **Click**: "Create repository"

#### Step 1.5: Add Remote and Push to GitHub
```bash
# Add GitHub remote (replace USERNAME with your GitHub username)
git remote add origin https://github.com/USERNAME/FastShop.git

# Set main branch as default
git branch -M main

# Push code to GitHub
git push -u origin main

# Verify push succeeded
git remote -v
```

#### Step 1.6: Verify on GitHub
- Open https://github.com/USERNAME/FastShop
- Confirm all files are visible
- Check commit history

---

## 2. Azure Server Setup

### Prerequisites
- Azure subscription active
- Azure CLI installed locally: https://docs.microsoft.com/cli/azure/install-azure-cli
- Authenticated to Azure: `az login`

### Azure Server Specifications for FastShop

| Specification | Value | Rationale |
|--------------|-------|-----------|
| **VM Size** | Standard_B2s | 2 vCPU, 4GB RAM, ~$30/month |
| **OS** | Ubuntu 20.04 LTS | Lightweight, long-term support |
| **Region** | East US | Low latency for US users |
| **Storage** | 64GB Standard SSD | Adequate for databases + images |

### Step 2.1: Create Azure Resource Group
```bash
# Set variables
RESOURCE_GROUP="FastShopRG"
LOCATION="eastus"
VM_NAME="FastShopVM"
ADMIN_USER="azureuser"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Verify
az group show --name $RESOURCE_GROUP
```

### Step 2.2: Generate SSH Key Pair
```bash
# Generate SSH key (if not already present)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/fastshop_key -N ""

# Output public key (copy this)
cat ~/.ssh/fastshop_key.pub

# Set permissions
chmod 600 ~/.ssh/fastshop_key
chmod 644 ~/.ssh/fastshop_key.pub
```

### Step 2.3: Create Azure Virtual Machine
```bash
# Create VM
az vm create \
  --resource-group $RESOURCE_GROUP \
  --name $VM_NAME \
  --image UbuntuLTS \
  --size Standard_B2s \
  --admin-username $ADMIN_USER \
  --ssh-key-values ~/.ssh/fastshop_key.pub \
  --public-ip-sku Standard \
  --output json > vm-details.json

# Save the public IP address
PUBLIC_IP=$(az vm list-ip-addresses \
  --resource-group $RESOURCE_GROUP \
  --name $VM_NAME \
  --query "[0].virtualMachines[0].publicIpAddresses[0].ipAddress" \
  --output tsv)

echo "Public IP: $PUBLIC_IP"
```

### Step 2.4: Configure Network Security Group (Firewall)
```bash
# Get NSG name
NSG_NAME=$(az network nsg list \
  --resource-group $RESOURCE_GROUP \
  --query "[0].name" \
  --output tsv)

# Allow port 3000 (Frontend)
az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name "AllowPort3000" \
  --priority 100 \
  --source-address-prefixes '*' \
  --destination-port-ranges 3000 \
  --access Allow \
  --protocol Tcp

# Allow port 8001 (Identity Hub)
az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name "AllowPort8001" \
  --priority 110 \
  --source-address-prefixes '*' \
  --destination-port-ranges 8001 \
  --access Allow \
  --protocol Tcp

# Allow port 8002 (Product Hub)
az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name "AllowPort8002" \
  --priority 120 \
  --source-address-prefixes '*' \
  --destination-port-ranges 8002 \
  --access Allow \
  --protocol Tcp

# Allow port 8003 (Transaction Hub)
az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name "AllowPort8003" \
  --priority 130 \
  --source-address-prefixes '*' \
  --destination-port-ranges 8003 \
  --access Allow \
  --protocol Tcp

# Allow SSH (port 22)
az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name "AllowSSH" \
  --priority 140 \
  --source-address-prefixes '*' \
  --destination-port-ranges 22 \
  --access Allow \
  --protocol Tcp
```

### Step 2.5: SSH into the Azure VM and Install Dependencies
```bash
# SSH into VM (use the public IP from Step 2.3)
ssh -i ~/.ssh/fastshop_key azureuser@$PUBLIC_IP

# Once inside VM, execute the following:

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt-get install -y git

# Verify installations
docker --version
docker-compose --version
git --version

# Optional: Install htop for monitoring
sudo apt-get install -y htop
```

### Step 2.6: Clone FastShop Repository
```bash
# Still in the VM terminal

# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone repository (replace USERNAME)
git clone https://github.com/USERNAME/FastShop.git

# Navigate to FastShop
cd FastShop

# Verify structure
ls -la
```

---

## 3. Running & Accessing the Application

### Step 3.1: Start Services with Docker Compose

#### On Local Machine (for testing):
```bash
# Navigate to FastShop directory
cd C:\Users\akash\FastShop

# Build and start all services
docker-compose up --build

# Expected output:
# identity_hub  | INFO:     Uvicorn running on http://0.0.0.0:8001
# product_hub   | INFO:     Uvicorn running on http://0.0.0.0:8002
# transaction_hub | INFO:     Uvicorn running on http://0.0.0.0:8003
# frontend_app  | VITE v5.0.0  ready in XXX ms ➜  Local: http://localhost:3000/
```

#### On Azure VM:
```bash
# SSH into VM
ssh -i ~/.ssh/fastshop_key azureuser@$PUBLIC_IP

# Navigate to FastShop
cd ~/apps/FastShop

# Start services in background
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# To stop services
docker-compose down
```

### Step 3.2: Verify Services Are Running

#### Health Checks:
```bash
# From local or another terminal

# Identity Hub (Port 8001)
curl http://localhost:8001/health

# Product Hub (Port 8002)
curl http://localhost:8002/health

# Transaction Hub (Port 8003)
curl http://localhost:8003/health

# Frontend (Port 3000)
curl http://localhost:3000
```

### Step 3.3: Access Application via URLs

#### Local Access:
| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main UI |
| **Identity Hub Docs** | http://localhost:8001/docs | Swagger API docs |
| **Product Hub Docs** | http://localhost:8002/docs | Swagger API docs |
| **Transaction Hub Docs** | http://localhost:8003/docs | Swagger API docs |

#### Azure Access (using public IP):
Replace `$PUBLIC_IP` with the actual IP from Step 2.3:

| Service | URL | 
|---------|-----|
| **Frontend** | http://$PUBLIC_IP:3000 |
| **Identity Hub Docs** | http://$PUBLIC_IP:8001/docs |
| **Product Hub Docs** | http://$PUBLIC_IP:8002/docs |
| **Transaction Hub Docs** | http://$PUBLIC_IP:8003/docs |

### Step 3.4: Application Workflow

#### 1. **Register/Login**
- Navigate to http://$PUBLIC_IP:3000
- Click "Sign Up" → Fill form → Create account
- Or "Sign In" if already registered

#### 2. **Browse Products**
- Click "Shop" tab in navigation
- View available products
- Check stock status

#### 3. **Add to Cart**
- Select quantity
- Click "Add to Cart"
- View cart item count in the navbar

#### 4. **Checkout**
- Click "Cart" in navigation
- Review items and total
- Click "Proceed to Checkout"
- **System verifies stock with Product Hub**
- Click "Confirm Order"
- See order confirmation with Order ID

#### 5. **Example Test Flow**
```
Frontend (localhost:3000)
  ↓
Register: username="john", email="john@example.com", password="TestPass123"
  ↓ (calls Identity Hub API: POST /auth/register)
Identity Hub (8001) - Hashes password, creates user, generates JWT
  ↓
Add Product #1 (qty=2) to Cart
  ↓ (calls Transaction Hub API: POST /cart/{user_id}/items)
Transaction Hub (8003) fetches product price from Product Hub (8002)
  ↓
Checkout
  ↓ (calls Transaction Hub API: POST /checkout)
Transaction Hub calls Product Hub: POST /products/stock/bulk-check
  ↓
Product Hub verifies stock, returns availability
  ↓ (if available) Order confirmed, cart cleared
  ↓
Frontend shows: "Order Confirmed! Order ID: 1"
```

### Step 3.5: Monitoring & Troubleshooting

#### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f identity_hub
docker-compose logs -f product_hub
docker-compose logs -f transaction_hub
docker-compose logs -f frontend_app

# Last 100 lines
docker-compose logs --tail=100
```

#### Check Resource Usage
```bash
# On Azure VM
docker stats

# System resources
htop

# Disk usage
df -h
```

#### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Ports already in use** | `docker-compose down` then restart |
| **Services not communicating** | Check network: `docker network ls` |
| **Frontend can't reach backend** | Verify port in docker-compose.yml |
| **Database lock error** | Restart single service: `docker-compose restart product_hub` |
| **Out of memory** | Increase memory limit in docker-compose.yml |

### Step 3.6: Performance Monitoring

#### Expected Metrics
```
Response Times:
- Login: 100-150ms
- Product List: 50-100ms
- Add to Cart: 50-80ms
- Checkout (with stock verification): 150-300ms

Memory Usage (at startup):
- Identity Hub: ~80MB
- Product Hub: ~75MB
- Transaction Hub: ~85MB
- Frontend: ~400MB (dev), ~50MB (production)
- Total: ~640MB

Throughput:
- Per service: 100-200 requests/second
```

---

## Quick Reference Commands

### Local Development
```bash
# Start all services
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild only frontend
docker-compose build frontend_app
```

### Azure VM Management
```bash
# SSH into VM
ssh -i ~/.ssh/fastshop_key azureuser@$PUBLIC_IP

# Start services
ssh -i ~/.ssh/fastshop_key azureuser@$PUBLIC_IP "cd ~/apps/FastShop && docker-compose up -d"

# View logs remotely
ssh -i ~/.ssh/fastshop_key azureuser@$PUBLIC_IP "cd ~/apps/FastShop && docker-compose logs -f"

# Stop services
ssh -i ~/.ssh/fastshop_key azureuser@$PUBLIC_IP "cd ~/apps/FastShop && docker-compose down"
```

### Git Operations
```bash
# After code changes
git add .
git commit -m "Description of changes"
git push origin main

# Pull latest changes
git pull origin main
```

---

## Production Checklist

- [ ] SSH key secured (chmod 600)
- [ ] Network Security Group configured for required ports only
- [ ] JWT_SECRET changed in docker-compose.yml (not default)
- [ ] Database backups configured (optional)
- [ ] Monitoring/logging set up (optional)
- [ ] SSL/TLS certificate installed (for HTTPS - optional)
- [ ] Environment variables set correctly
- [ ] All services passing health checks
- [ ] Load tested with expected user load

---

## Support & Troubleshooting

### Resources
- FastAPI Docs: https://fastapi.tiangolo.com/
- React Docs: https://react.dev/
- Docker Docs: https://docs.docker.com/
- Azure Docs: https://docs.microsoft.com/azure/

### Logs Location on Azure VM
```
~/.docker/logs  # Docker logs
~/apps/FastShop/  # Application logs
```

### Reset Everything (Nuclear Option)
```bash
# On Azure VM
cd ~/apps/FastShop
docker-compose down -v  # Remove volumes
docker system prune -a  # Remove all Docker objects
git clean -fd  # Remove untracked files
git reset --hard  # Reset to last commit
```

---

**Date Created:** April 30, 2026  
**Version:** 1.0.0  
**Last Updated:** April 30, 2026
