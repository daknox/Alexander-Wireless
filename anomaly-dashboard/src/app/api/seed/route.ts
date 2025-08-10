import { NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function POST() {
  try {
    // Import the seed function
    const { execSync } = require('child_process')
    
    // Run the seed script
    execSync('npx prisma db seed', { stdio: 'inherit' })
    
    return NextResponse.json({ 
      message: 'Database seeded successfully',
      note: 'This should only be run once to populate the database with initial data'
    })
  } catch (error) {
    console.error('Error seeding database:', error)
    return NextResponse.json(
      { error: 'Failed to seed database' },
      { status: 500 }
    )
  }
}
