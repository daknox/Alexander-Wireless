import { PrismaClient } from '@prisma/client'
import { addDays, subDays, subMonths } from 'date-fns'

const prisma = new PrismaClient()

// T-Mobile billing codes (4 ladder sheets)
const BILLING_CODES = {
  SEC: [
    'SEC001', 'SEC002', 'SEC003', 'SEC004', 'SEC005', 'SEC006', 'SEC007', 'SEC008', 'SEC009', 'SEC010',
    'SEC011', 'SEC012', 'SEC013', 'SEC014', 'SEC015', 'SEC016', 'SEC017', 'SEC018', 'SEC019', 'SEC020'
  ],
  ACR: [
    'ACR001', 'ACR002', 'ACR003', 'ACR004', 'ACR005', 'ACR006', 'ACR007', 'ACR008', 'ACR009', 'ACR010',
    'ACR011', 'ACR012', 'ACR013', 'ACR014', 'ACR015', 'ACR016', 'ACR017', 'ACR018', 'ACR019', 'ACR020'
  ],
  SUB: [
    'SUB001', 'SUB002', 'SUB003', 'SUB004', 'SUB005', 'SUB006', 'SUB007', 'SUB008', 'SUB009', 'SUB010',
    'SUB011', 'SUB012', 'SUB013', 'SUB014', 'SUB015', 'SUB016', 'SUB017', 'SUB018', 'SUB019', 'SUB020'
  ],
  ADD: [
    'ADD001', 'ADD002', 'ADD003', 'ADD004', 'ADD005', 'ADD006', 'ADD007', 'ADD008', 'ADD009', 'ADD010',
    'ADD011', 'ADD012', 'ADD013', 'ADD014', 'ADD015', 'ADD016', 'ADD017', 'ADD018', 'ADD019', 'ADD020'
  ]
}

const AUDIT_TYPE_DESCRIPTIONS: { [key: string]: string } = {
  SEC: 'Single Event Charges',
  ACR: 'Account Corrections', 
  SUB: 'Subscription Plans',
  ADD: 'Line Add-ons'
}

// T-Mobile anomaly detection thresholds from ARCHITECTURE.md
const ANOMALY_THRESHOLDS = {
  SEC: { absoluteChange: 50000, percentChange: 0.25 }, // Single Event Charges
  ACR: { absoluteChange: 25000, percentChange: 0.25 }, // Account Corrections  
  SUB: { absoluteChange: 50000, percentChange: 0.25 }, // Subscription Plans
  ADD: { absoluteChange: 25000, percentChange: 0.25 }  // Line Add-ons
}

// Generate realistic T-Mobile billing data with proper calculations
function generateBillingData(cycleNumber: number, year: number, month: number, monthOffset: number = 0) {
  const data: any[] = []
  
  Object.entries(BILLING_CODES).forEach(([auditType, codes]) => {
    codes.forEach((billingCode, index) => {
      // Base amount with realistic T-Mobile ranges
      const baseAmount = 500000 + (index * 250000) + Math.random() * 1000000
      
      // Generate historical data with realistic trends
      const historicalData: number[] = []
      for (let i = 5; i >= 1; i--) {
        const monthTrend = monthOffset + (5 - i)
        const trendFactor = baseAmount + 
                           monthTrend * (20000 + Math.random() * 100000) + 
                           (Math.random() - 0.5) * 150000
        historicalData.push(Math.max(0, Math.min(5000000, trendFactor)))
      }
      
      // Current month amount
      const currentMonthTrend = monthOffset + 5
      let currentAmount = baseAmount + 
                         currentMonthTrend * (50000 + Math.random() * 200000) + 
                         (Math.random() - 0.5) * 300000
      currentAmount = Math.max(0, Math.min(5000000, currentAmount))
      
      // Calculate rolling 5-month average
      const rolling5MonthAvg = historicalData.reduce((a, b) => a + b, 0) / historicalData.length
      
      // Month over month calculations
      const momChange = currentAmount - historicalData[0]
      const momChangePercent = historicalData[0] > 0 ? (momChange / historicalData[0]) : 0
      
      // Average vs current calculations
      const avgVsCurrentDiff = currentAmount - rolling5MonthAvg
      const avgVsCurrentPercent = rolling5MonthAvg > 0 ? (avgVsCurrentDiff / rolling5MonthAvg) : 0
      
      // Anomaly detection using T-Mobile thresholds
      let isAnomaly = false
      let anomalyScore = 0
      let anomalyReason: string | null = null
      
      const thresholds = ANOMALY_THRESHOLDS[auditType as keyof typeof ANOMALY_THRESHOLDS]
      
      // Check if thresholds are exceeded
      if (Math.abs(avgVsCurrentDiff) >= thresholds.absoluteChange && Math.abs(avgVsCurrentPercent) >= thresholds.percentChange) {
        isAnomaly = true
        
        // Calculate anomaly score based on severity with more variety
        const absoluteSeverity = Math.abs(avgVsCurrentDiff) / thresholds.absoluteChange
        const percentSeverity = Math.abs(avgVsCurrentPercent) / thresholds.percentChange
        const baseScore = (absoluteSeverity + percentSeverity) / 2
        
        // Add some randomness to create variety in severity levels
        const randomFactor = 0.8 + Math.random() * 0.4 // 0.8 to 1.2
        anomalyScore = Math.min(1.0, baseScore * randomFactor)
        
        anomalyReason = `Threshold exceeded: $${Math.abs(avgVsCurrentDiff).toLocaleString()} change (${(avgVsCurrentPercent * 100).toFixed(1)}%)`
      }
      
      data.push({
        billingCode,
        auditType,
        year,
        month,
        cycleNumber,
        amount5MonthsAgo: historicalData[4],
        amount4MonthsAgo: historicalData[3],
        amount3MonthsAgo: historicalData[2],
        amount2MonthsAgo: historicalData[1],
        amount1MonthAgo: historicalData[0],
        currentMonthAmount: currentAmount,
        rolling5MonthAvg,
        momChange,
        momChangePercent,
        avgVsCurrentDiff,
        avgVsCurrentPercent,
        isAnomaly,
        anomalyScore: isAnomaly ? anomalyScore : null,
        anomalyReason
      })
    })
  })
  
  return data
}

async function main() {
  console.log('🌱 Seeding T-Mobile billing database with comprehensive anomaly detection...')

  // Clear existing data
  await prisma.analystNote.deleteMany()
  await prisma.anomaly.deleteMany()
  await prisma.billingData.deleteMany()
  await prisma.billingCycle.deleteMany()
  await prisma.billingCode.deleteMany()

  // Create billing codes
  console.log('📝 Creating billing codes...')
  const billingCodes = []
  for (const [auditType, codes] of Object.entries(BILLING_CODES)) {
    for (const billingCode of codes) {
      const code = await prisma.billingCode.create({
        data: {
          billingCode,
          auditType,
          description: `${AUDIT_TYPE_DESCRIPTIONS[auditType]} - ${billingCode}`
        }
      })
      billingCodes.push(code)
    }
  }

  // Create 6 months of data with 10 cycles per month
  console.log('🔄 Creating billing cycles (6 months, 10 cycles per month)...')
  const cycles = []
  const currentDate = new Date()
  
  // Create exactly 6 months of data
  for (let monthOffset = 5; monthOffset >= 0; monthOffset--) {
    const targetDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - monthOffset, 1)
    const year = targetDate.getFullYear()
    const month = targetDate.getMonth() + 1
    
    // Create exactly 10 cycles per month with sequential cycle numbers (1-10)
    for (let cycleIndex = 0; cycleIndex < 10; cycleIndex++) {
      const cycleNumber = cycleIndex + 1
      const cycleDate = `${month.toString().padStart(2, '0')}-${cycleNumber.toString().padStart(2, '0')}-${year}`
      
      const cycle = await prisma.billingCycle.create({
        data: {
          cycleDate,
          cycleNumber,
          year,
          month
        }
      })
      cycles.push(cycle)
    }
  }

  // Generate and store billing data
  console.log('📊 Generating billing data with calculations...')
  let totalAnomalies = 0
  
  for (const cycle of cycles) {
    // Calculate proper month offset for historical data
    const monthOffset = 5 - (new Date().getMonth() - cycle.month + 1)
    const billingData = generateBillingData(cycle.cycleNumber, cycle.year, cycle.month, monthOffset)
    
    for (const data of billingData) {
      const code = billingCodes.find(c => c.billingCode === data.billingCode && c.auditType === data.auditType)
      if (!code) continue
      
      const billingRecord = await prisma.billingData.create({
        data: {
          cycleId: cycle.id,
          codeId: code.id,
          billingCode: data.billingCode,
          auditType: data.auditType,
          year: data.year,
          month: data.month,
          cycleNumber: data.cycleNumber,
          amount5MonthsAgo: data.amount5MonthsAgo,
          amount4MonthsAgo: data.amount4MonthsAgo,
          amount3MonthsAgo: data.amount3MonthsAgo,
          amount2MonthsAgo: data.amount2MonthsAgo,
          amount1MonthAgo: data.amount1MonthAgo,
          currentMonthAmount: data.currentMonthAmount,
          rolling5MonthAvg: data.rolling5MonthAvg,
          momChange: data.momChange,
          momChangePercent: data.momChangePercent,
          avgVsCurrentDiff: data.avgVsCurrentDiff,
          avgVsCurrentPercent: data.avgVsCurrentPercent,
          isAnomaly: data.isAnomaly,
          anomalyScore: data.anomalyScore,
          anomalyReason: data.anomalyReason
        }
      })
      
      // Create anomaly record if anomaly detected
      if (data.isAnomaly) {
        totalAnomalies++
        
        // Add variety to severity levels with better distribution
        let severity: string
        const randomValue = Math.random()
        if (randomValue < 0.2) {
          severity = 'critical'
        } else if (randomValue < 0.4) {
          severity = 'high'
        } else if (randomValue < 0.7) {
          severity = 'medium'
        } else {
          severity = 'low'
        }
        
        const anomalyType = data.avgVsCurrentDiff > 0 ? 'spike' : 'drop'
        
        await prisma.anomaly.create({
          data: {
            cycleId: cycle.id,
            codeId: code.id,
            billingDataId: billingRecord.id,
            billingCode: data.billingCode,
            auditType: data.auditType,
            anomalyType,
            severity,
            anomalyScore: data.anomalyScore!,
            threshold: ANOMALY_THRESHOLDS[data.auditType as keyof typeof ANOMALY_THRESHOLDS].absoluteChange,
            currentValue: data.currentMonthAmount,
            expectedValue: data.rolling5MonthAvg,
            percentChange: data.avgVsCurrentPercent,
            description: data.anomalyReason || 'Threshold anomaly detected',
            businessImpact: severity === 'critical' ? 'High financial impact' : 'Moderate impact',
            recommendedAction: 'Investigate billing code for potential issues',
            status: 'open',
            isResearched: false
          }
        })
      }
    }
    
    // Update cycle statistics
    const cycleData = await prisma.billingData.findMany({ where: { cycleId: cycle.id } })
    const cycleAnomalies = await prisma.anomaly.findMany({ where: { cycleId: cycle.id } })
    const totalAmount = cycleData.reduce((sum, record) => sum + Number(record.currentMonthAmount), 0)
    
    await prisma.billingCycle.update({
      where: { id: cycle.id },
      data: {
        totalRecords: cycleData.length,
        anomalyCount: cycleAnomalies.length,
        totalAmount
      }
    })
  }

  // Add some sample analyst notes
  console.log('📝 Adding sample analyst notes...')
  const sampleAnomalies = await prisma.anomaly.findMany({ take: 5 })
  for (const anomaly of sampleAnomalies) {
    await prisma.analystNote.create({
      data: {
        anomalyId: anomaly.id,
        analystName: 'John Smith',
        note: `Initial investigation of ${anomaly.billingCode} - ${anomaly.auditType} anomaly. Threshold exceeded by ${(Number(anomaly.percentChange) * 100).toFixed(1)}%.`
      }
    })
  }

  console.log(`✅ Created ${cycles.length} billing cycles (6 months × 10 cycles)`)
  console.log(`✅ Created ${billingCodes.length} billing codes`)
  console.log(`✅ Generated billing data with ${totalAnomalies} anomalies detected`)
  console.log(`✅ Added sample analyst notes`)
  console.log('🎉 T-Mobile billing database seeding completed!')
}

main()
  .catch((e) => {
    console.error('❌ Error seeding database:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
