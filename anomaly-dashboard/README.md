# Alexander Wireless - Telecom Billing Anomaly Detection Dashboard

A modern web dashboard for detecting and visualizing billing anomalies in telecom operations, built with Next.js, Prisma, and PostgreSQL.

## Features

- **Real-time Anomaly Detection**: Uses the exact thresholds from Alexander Wireless ARCHITECTURE.md
- **Interactive Dashboard**: Beautiful charts and tables showing anomaly statistics
- **Database Integration**: PostgreSQL with Prisma ORM for robust data management
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Charts**: Recharts for data visualization
- **Database**: PostgreSQL (Neon DB)
- **ORM**: Prisma
- **Deployment**: Vercel-ready

## Setup Instructions

### 1. Environment Setup

Create a `.env` file in the root directory:

```bash
# Copy the example file
cp .env.example .env
```

Update the `.env` file with your Neon database connection string:

```env
DATABASE_URL="postgresql://username:password@host:port/database?sslmode=require"
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Database Setup

```bash
# Push the schema to your database
npx prisma db push

# Seed the database with demo data (run once)
npm run db:seed
```

### 4. Start Development Server

```bash
npm run dev
```

Visit `http://localhost:3000/billing` to see the dashboard.

## Database Schema

The application uses the following main models:

- **BillingCycle**: Represents billing processing cycles
- **BillingCode**: Billing codes and their types (SEC, ACR, SUB, ADD)
- **BillingData**: Historical and current billing amounts with calculations
- **Anomaly**: Detected anomalies with severity and details
- **ProcessingEvent**: Log of processing events

## Anomaly Detection Logic

The system uses the exact thresholds from Alexander Wireless:

| Audit Type | Absolute Change Threshold | Percent Change Threshold |
|------------|--------------------------|-------------------------|
| Single Event Charges | 50,000 | 25% |
| Account Corrections | 25,000 | 25% |
| Line Add-ons | 25,000 | 25% |
| Subscription Plans | 50,000 | 25% |

Anomalies are flagged when:
- (|Change| >= threshold AND |Change %| >= 25%)
- OR the code is new this cycle
- OR the code dropped to zero

## API Endpoints

- `GET /api/anomalies` - Fetch all anomaly data and statistics
- `POST /api/seed` - Initialize database with demo data (one-time use)

## Deployment

This project is ready for deployment on Vercel:

1. Push to GitHub
2. Import to Vercel
3. Add environment variables
4. Deploy

## Security Notes

- Never commit the `.env` file to version control
- Use environment variables for sensitive data
- The seed script should only be run once in production

## Contributing

This project represents the Alexander Wireless anomaly detection system adapted for web deployment. The core logic matches the original Python implementation.
