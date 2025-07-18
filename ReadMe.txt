💰 FinJO
A full-stack, production-ready fintech platform built around a Jordanian Dinar (JD)–pegged stablecoin, integrating real-time Open Banking APIs (JoPACC) and advanced AI-driven financial services.

🧭 Overview
This platform provides a secure, intelligent, and seamless financial experience for users in Jordan and beyond. It brings together the power of stablecoin wallets, open banking, AI-powered personal finance, and ML-driven anti-fraud systems into a single, unified platform.

✅ Key Features
🔐 DinarX Wallet & Stored Value Card
JD-pegged stablecoin wallet with fiat-to-stablecoin exchange.

Supports deposits, transfers, and unified payments.

🔗 Open Banking Integration (JoPACC)
Real-time connection to Jordanian banks via JoPACC's AIS, PIS, FPS, and FX APIs.

Handles customer account types: single, multi-account, corporate, and custodial.

All API calls depend on customer_id and include x-customer-id headers for consistency.

Supports account linking, balance viewing, FX rates, and transaction initiation.

🧠 AI Money Concierge ("Hey Dinar")
Smart, conversational financial assistant.

Integrated with user data to help with budgeting, FX suggestions, and account inquiries.

🛡️ Advanced Security Suite
ML-based AML (Anti-Money Laundering) monitoring compliant with Central Bank of Jordan.

Real-time risk scoring engine.

Admin dashboard for fraud alerts, behavioral flags, and system health.

🤝 Peer-to-Peer Transfers
Seamless user-to-user stablecoin transfers with AML and balance validation.

Full transfer history and recipient search.

🌍 International Transfers
Low-fee, near-instant global remittance using blockchain-backed stablecoin rails.

👤 User Profiles & Credit Scoring
Aggregates open banking and transaction data to build real-time financial profiles.

Generates ML-based risk and credit scores.

💸 Micro Loans
Instant JD-based micro loans with AI-powered approval logic.

Flexible repayment and automated tracking.

🧾 IBAN Verification
Verifies IBANs during registration using real-time banking APIs.

🛠️ Technology Stack
Backend
FastAPI (Python)

MongoDB

Supervisor + Kubernetes (Dockerized environment)

Frontend
React + Tailwind CSS

JWT-based authentication

Responsive dashboards, user portals, and secure onboarding flows

Integrations
JoPACC Open Banking APIs

Real-time FX, Accounts, Transactions, PIS, FPS

ML models for AML & credit scoring

