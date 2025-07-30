# AWS Full Stack Image Resizer Application

This project demonstrates a complete AWS-based web application that allows users to upload images via a web interface. Images are stored in S3, resized by a Lambda function, and stored in another S3 bucket. The app uses EC2, RDS, EFS, Auto Scaling, Load Balancer, and CloudFront.

## Project Folder Structure
```
aws-practice/
├── lambda/
│   └── lambda_function.py          # Python Lambda function with Layer
└── web/
    ├── add.php
    ├── index.html
    └── view.php
```

## Setup Instructions

### Step 1: Create a VPC with 3 public subnets
If you have deleted the VPC created earlier during the VPC training section, recreate it by following the same steps.

### Step 2–3: Create 2 S3 Buckets
- Create a bucket named `your-project-name`, and inside it, create a folder named `images`.
- Create a second bucket named `your-project-name-resized`. During creation:
  - Uncheck all four ACL and public access restriction options under "Configure options".
  - Add the following bucket policy to allow public access:
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "PublicReadForGetObject",
          "Effect": "Allow",
          "Principal": "*",
          "Action": "s3:GetObject",
          "Resource": "arn:aws:s3:::your-project-name-resized/*"
        }
      ]
    }
    ```
  - Set CORS configuration:
    ```xml
    <CORSConfiguration>
      <CORSRule>
        <AllowedOrigin>*</AllowedOrigin>
        <AllowedMethod>GET</AllowedMethod>
        <AllowedMethod>PUT</AllowedMethod>
        <AllowedMethod>POST</AllowedMethod>
        <AllowedHeader>*</AllowedHeader>
      </CORSRule>
    </CORSConfiguration>
    ```

### Step 4: Create IAM Roles
- `Lambda-S3` Role:
  - Trusted entity: Lambda
  - Policy: `AWSLambdaExecute`
- `Ec2-S3` Role:
  - Trusted entity: EC2
  - Policy: `AmazonS3FullAccess`

### Step 5–6: Create a Lambda Function for Image Resizing (with Python & Layer)
- Go to the **Lambda** service and create a new function:
  - **Runtime**: Python 3.x (e.g., Python 3.9)
  - **Permissions**: Attach the `Lambda-S3` IAM role
- After creation:
  1. Go to the **Layers** section and **add a new layer**:
     - Choose a prebuilt or custom layer (e.g., Pillow) compatible with your Python runtime
  2. Attach this layer to your Lambda function
  3. In the **Code** tab:
     - Paste in your code from `lambda_function.py` or upload the `.py` file directly
  4. Add a **Trigger**:
     - Type: S3
     - Bucket: `your-project-name`
     - Event type: All object create events
  5. Set the **Timeout** to 10 seconds under Basic settings
  6. Save the configuration

### Step 7: Create a Security Group
- Name: `Proje-SecGroup`
- Allow:
  - HTTP (port 80) from 0.0.0.0/0
  - SSH (port 22) from 0.0.0.0/0

### Step 8–14: Launch EC2 Template Instance
- Instance type: t2.micro
- AMI: Amazon Linux 2
- Subnet: Public
- IAM role: `Ec2-S3`
- Security Group: `Proje-SecGroup`
- Connect and run:
  ```bash
  sudo yum update -y
  sudo yum install -y httpd mysql
  sudo amazon-linux-extras enable php7.2
  sudo yum install -y php php-mysqlnd
  sudo systemctl enable httpd
  sudo systemctl restart httpd
  ```
- Test PHP:
  ```bash
  echo "<?php phpinfo(); ?>" > /var/www/html/test.php
  ```

### Step 15–21: Mount EFS
- Create EFS with all public subnets
- Allow NFS (TCP 2049) from `Proje-SecGroup`
- EC2:
  ```bash
  sudo yum install -y amazon-efs-utils
  sudo mkdir -p /var/www/html
  sudo mount -t efs fs-xxxxxx:/ /var/www/html
  echo "fs-xxxxxx:/ /var/www/html efs defaults,_netdev 0 0" | sudo tee -a /etc/fstab
  cd /var/www/html
  mkdir images
  chmod 777 images
  ```

### Step 22–27: Create RDS Database
- Engine: MySQL
- Instance ID: `projedbinstance`
- Username: `projemaster`
- Password: `master1234`
- DB name: `proje`
- Disable public access
- Add RDS security group rule: allow MySQL (3306) from `Proje-SecGroup`
- From EC2:
  ```bash
  mysql -h projedbinstance.<region>.rds.amazonaws.com -u projemaster -p
  USE proje;
  CREATE TABLE visitors (name VARCHAR(30), email VARCHAR(30), phone VARCHAR(30), photo VARCHAR(30));
  ```

### Step 28–32: Deploy Web App
- Update `add.php` and `view.php`:
  ```php
  $servername = "projedbinstance.<region>.rds.amazonaws.com";
  echo "<img src=https://your-project-name-resized.s3.<region>.amazonaws.com/resized-images/"
  ```
- Upload `index.html`, `add.php`, `view.php` to `/var/www/html/`

### Step 33–35: Sync Script & Cronjob
- Create `/var/www/html/s3.sh`
  ```bash
  #!/bin/bash
  aws s3 sync /var/www/html/images s3://your-project-name/images
  ```
- Make it executable and add to crontab:
  ```bash
  chmod +x /var/www/html/s3.sh
  sudo crontab -e
  # Add:
  */2 * * * * /var/www/html/s3.sh
  ```

### Step 36–37: Create AMI
- Stop EC2 instance
- Create snapshot of its volume
- Create AMI from snapshot named `ProjeAMI`

### Step 38–39: Load Balancer
- Create Target Group (Path: `/index.html`)
- Create Application Load Balancer with 3 public subnets and `Proje-SecGroup`
- Attach Target Group

### Step 40–44: Auto Scaling
- Create Launch Configuration with `ProjeAMI`
- Create Auto Scaling Group:
  - Desired: 3, Min: 3, Max: 5
  - Attach to Load Balancer Target Group
  - Scaling policy based on 90% CPU

### Step 45: CloudFront
- Create Web Distribution:
  - Origin: Load Balancer DNS
  - Alternate Domain Name: `www.yourdomain.com`
  - Price Class: US, EU, Canada

### Step 46–47: Route53
- Add `A` record with alias to CloudFront distribution
- Now access your site at `www.yourdomain.com`