# Blockchain-Integrated E-Commerce Management System

A multi-role e-commerce platform with Ethereum blockchain payment integration, built with Python/Flask and containerized using Docker.

## Key Features

- **Blockchain Integration**:
  - Automated payment processing via Solidity smart contracts
  - 80%/20% fund distribution between store owners and couriers
  - Ganache-cli for local Ethereum blockchain simulation
  - Secure transaction validation with encrypted key management

- **Core Functionality**:
  - JWT-authenticated multi-role system (customers, owners, couriers)
  - Product catalog with category management
  - Order lifecycle tracking (created → in transit → delivered)
  - Spark-powered sales analytics

## Tech Stack

| Category        | Technologies                          |
|-----------------|---------------------------------------|
| Backend         | Python, Flask, SQLAlchemy            |
| Blockchain      | Solidity, Ganache, Web3.py           |
| Data Processing | Spark (Big Data Europe Docker image)  |
| Database        | MySQL with SQLAlchemy ORM             |
| Infrastructure  | Docker, Docker Compose                |
| Security        | JWT authentication, encrypted keys   |
