import { NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function GET() {
  try {
    // Get all anomalies with related data
    const anomalies = await prisma.anomaly.findMany({
      include: {
        cycle: true,
        code: true,
        billingData: true,
        analystNotes: true
      },
      orderBy: {
        createdAt: 'desc'
      }
    })

    // Get anomaly statistics
    const anomalyStats = await prisma.anomaly.groupBy({
      by: ['severity', 'anomalyType'],
      _count: {
        id: true
      }
    })

    // Get billing cycle summary (last 6 months)
    const sixMonthsAgo = new Date()
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6)
    
    const cycles = await prisma.billingCycle.findMany({
      where: {
        processingTimestamp: {
          gte: sixMonthsAgo
        }
      },
      include: {
        _count: {
          select: {
            anomalies: true,
            billingData: true
          }
        }
      },
      orderBy: {
        processingTimestamp: 'desc'
      }
    })

    // Get monthly totals by audit type for line charts (last 6 months)
    const monthlyTotals = await prisma.billingData.groupBy({
      by: ['year', 'month', 'auditType'],
      where: {
        cycle: {
          processingTimestamp: {
            gte: sixMonthsAgo
          }
        }
      },
      _sum: {
        currentMonthAmount: true
      },
      orderBy: [
        { year: 'asc' },
        { month: 'asc' }
      ]
    })

    // Get top billing codes by anomaly count
    const topAnomalyCodes = await prisma.anomaly.groupBy({
      by: ['billingCode', 'auditType'],
      _count: {
        id: true
      },
      orderBy: {
        _count: {
          id: 'desc'
        }
      },
      take: 10
    })

    // Get anomalies by audit type for the bar chart
    const anomaliesByAuditType = await prisma.anomaly.groupBy({
      by: ['auditType'],
      _count: {
        id: true
      }
    })

    // Get all billing data for the detailed table
    const billingData = await prisma.billingData.findMany({
      include: {
        cycle: true,
        code: true,
        anomaly: {
          include: {
            analystNotes: true
          }
        }
      },
      orderBy: [
        { cycle: { processingTimestamp: 'desc' } },
        { auditType: 'asc' },
        { billingCode: 'asc' }
      ]
    })

    // Convert Decimal values to numbers for proper formatting
    const processedBillingData = billingData.map(record => ({
      ...record,
      currentMonthAmount: Number(record.currentMonthAmount),
      rolling5MonthAvg: record.rolling5MonthAvg ? Number(record.rolling5MonthAvg) : null,
      momChange: record.momChange ? Number(record.momChange) : null,
      momChangePercent: record.momChangePercent ? Number(record.momChangePercent) : null,
      avgVsCurrentDiff: record.avgVsCurrentDiff ? Number(record.avgVsCurrentDiff) : null,
      avgVsCurrentPercent: record.avgVsCurrentPercent ? Number(record.avgVsCurrentPercent) : null,
      anomalyScore: record.anomalyScore ? Number(record.anomalyScore) : null,
      cycle: {
        ...record.cycle,
        totalAmount: Number(record.cycle.totalAmount)
      }
    }))

    // Convert monthly totals to numbers
    const processedMonthlyTotals = monthlyTotals.map(item => ({
      ...item,
      _sum: {
        currentMonthAmount: Number(item._sum.currentMonthAmount)
      }
    }))

    // Convert cycles to numbers
    const processedCycles = cycles.map(cycle => ({
      ...cycle,
      totalAmount: Number(cycle.totalAmount)
    }))

    return NextResponse.json({
      anomalies,
      stats: {
        totalAnomalies: anomalies.length,
        bySeverity: anomalyStats.filter(s => s.severity),
        byType: anomalyStats.filter(s => s.anomalyType),
        byAuditType: anomaliesByAuditType,
        cycles: processedCycles,
        topAnomalyCodes
      },
      monthlyTotals: processedMonthlyTotals,
      billingData: processedBillingData
    })
  } catch (error) {
    console.error('Error fetching anomalies:', error)
    return NextResponse.json(
      { error: 'Failed to fetch anomalies' },
      { status: 500 }
    )
  }
}
