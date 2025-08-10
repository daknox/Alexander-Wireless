import { NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function POST(request: Request) {
  try {
    const { anomalyId, analystName, note } = await request.json()
    
    if (!anomalyId || !analystName || !note) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    const analystNote = await prisma.analystNote.create({
      data: {
        anomalyId,
        analystName,
        note
      }
    })

    return NextResponse.json(analystNote)
  } catch (error) {
    console.error('Error creating analyst note:', error)
    return NextResponse.json(
      { error: 'Failed to create analyst note' },
      { status: 500 }
    )
  }
}
