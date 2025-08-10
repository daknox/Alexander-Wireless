'use client'

import { useState, useEffect } from 'react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area,
  ComposedChart
} from 'recharts'

interface AnomalyData {
  anomalies: Array<{
    id: string
    billingCode: string
    auditType: string
    anomalyType: string
    severity: string
    anomalyScore: number
    description: string
    status: string
    isResearched: boolean
    createdAt: string
    cycle: {
      cycleDate: string
    }
    analystNotes: Array<{
      analystName: string
      note: string
      timestamp: string
    }>
  }>
  stats: {
    totalAnomalies: number
    bySeverity: Array<{
      severity: string
      _count: { id: number }
    }>
    byType: Array<{
      anomalyType: string
      _count: { id: number }
    }>
    byAuditType: Array<{
      auditType: string
      _count: { id: number }
    }>
    cycles: Array<{
      cycleDate: string
      totalRecords: number
      anomalyCount: number
      totalAmount: number
    }>
  }
  monthlyTotals: Array<{
    year: number
    month: number
    auditType: string
    _sum: { currentMonthAmount: number }
  }>
  billingData: Array<{
    id: string
    billingCode: string
    auditType: string
    currentMonthAmount: number
    rolling5MonthAvg: number
    momChange: number
    momChangePercent: number
    avgVsCurrentDiff: number
    avgVsCurrentPercent: number
    isAnomaly: boolean
    anomalyScore: number
    cycle: {
      cycleDate: string
    }
    anomaly: {
      id: string
      severity: string
      status: string
      isResearched: boolean
      analystNotes: Array<{
        analystName: string
        note: string
        timestamp: string
      }>
    } | null
  }>
}

const SEVERITY_COLORS = {
  critical: '#EF4444',
  high: '#F97316', 
  medium: '#EAB308',
  low: '#22C55E'
}

const AUDIT_TYPE_COLORS = {
  SEC: '#8B5CF6', // Purple
  ACR: '#06B6D4', // Cyan
  SUB: '#10B981', // Emerald
  ADD: '#F59E0B'  // Amber
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

export default function BillingDashboard() {
  const [anomalyData, setAnomalyData] = useState<AnomalyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedAnomaly, setSelectedAnomaly] = useState<string | null>(null)
  const [analystNote, setAnalystNote] = useState('')
  const [analystName, setAnalystName] = useState('')
  const [editingNote, setEditingNote] = useState<string | null>(null)
  
  // Table filters
  const [cycleFilter, setCycleFilter] = useState('')
  const [monthFilter, setMonthFilter] = useState('')
  const [auditTypeFilter, setAuditTypeFilter] = useState('')
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [recordsPerPage, setRecordsPerPage] = useState(50)
  
  // Loading state for note submission
  const [savingNote, setSavingNote] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/anomalies')
      
      if (!response.ok) {
        throw new Error('Failed to fetch data')
      }
      
      const data = await response.json()
      
      // Debug: Check data types
      if (data.billingData && data.billingData.length > 0) {
        const sampleRecord = data.billingData[0]
        console.log('Sample record data types:', {
          currentMonthAmount: typeof sampleRecord.currentMonthAmount,
          value: sampleRecord.currentMonthAmount,
          formatted: sampleRecord.currentMonthAmount?.toLocaleString()
        })
      }
      
      setAnomalyData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleSeedData = async () => {
    try {
      const response = await fetch('/api/seed', { method: 'POST' })
      if (!response.ok) {
        throw new Error('Failed to seed data')
      }
      await fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to seed data')
    }
  }

  const addAnalystNote = async (anomalyId: string) => {
    if (!analystNote.trim() || !analystName.trim()) return
    
    // Prevent multiple submissions
    if (savingNote === anomalyId) return
    
    try {
      setSavingNote(anomalyId)
      
      const response = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          anomalyId,
          analystName,
          note: analystNote
        })
      })
      
      if (response.ok) {
        setAnalystNote('')
        setAnalystName('')
        setEditingNote(null)
        await fetchData()
      }
    } catch (err) {
      console.error('Failed to add note:', err)
    } finally {
      setSavingNote(null)
    }
  }

  const calculateAlarmWeight = (momChange: number, momChangePercent: number) => {
    const absoluteWeight = Math.abs(momChange) / 100000 // Normalize by 100k
    const percentWeight = Math.abs(momChangePercent) * 10 // Scale percentage
    return Math.min(1, (absoluteWeight + percentWeight) / 2)
  }

  const getRowColor = (alarmWeight: number, isAnomaly: boolean) => {
    if (!isAnomaly) return 'bg-gray-50'
    if (alarmWeight > 0.8) return 'bg-red-100'
    if (alarmWeight > 0.6) return 'bg-orange-100'
    if (alarmWeight > 0.4) return 'bg-yellow-100'
    return 'bg-green-100'
  }

  // Get unique months from the data
  const getUniqueMonths = () => {
    if (!anomalyData) return []
    const months = new Set<string>()
    anomalyData.billingData.forEach(record => {
      // cycleDate format is "MM-DD-YYYY", so we need to extract MM and YYYY
      const parts = record.cycle.cycleDate.split('-')
      if (parts.length === 3) {
        const month = parts[0] // MM
        const year = parts[2]  // YYYY
        const monthKey = `${year}-${month}`
        months.add(monthKey)
      }
    })
    return Array.from(months).sort()
  }

  // Filter billing data based on filters
  const filteredBillingData = anomalyData?.billingData.filter(record => {
    if (cycleFilter && !record.cycle.cycleDate.includes(cycleFilter)) return false
    if (monthFilter) {
      // Extract month and year from cycleDate (MM-DD-YYYY format)
      const parts = record.cycle.cycleDate.split('-')
      if (parts.length === 3) {
        const month = parts[0] // MM
        const year = parts[2]  // YYYY
        const recordMonthKey = `${year}-${month}`
        if (recordMonthKey !== monthFilter) return false
      }
    }
    if (auditTypeFilter && record.auditType !== auditTypeFilter) return false
    return true
  }) || [] // Remove the slice(0, 50) limit for pagination

  // Pagination calculations
  const totalRecords = filteredBillingData.length
  const totalPages = Math.ceil(totalRecords / recordsPerPage)
  const startIndex = (currentPage - 1) * recordsPerPage
  const endIndex = startIndex + recordsPerPage
  const currentRecords = filteredBillingData.slice(startIndex, endIndex)

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [cycleFilter, monthFilter, auditTypeFilter])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-xl text-gray-300">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-red-400">Error: {error}</div>
      </div>
    )
  }

  if (!anomalyData) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-400">No data available</div>
      </div>
    )
  }

  // Prepare data for dual-axis line charts (6 months)
  const chartData = anomalyData.monthlyTotals.reduce((acc, item) => {
    const monthKey = `${item.year}-${item.month.toString().padStart(2, '0')}`
    const existing = acc.find(d => d.month === monthKey)
    
    if (existing) {
      existing[item.auditType] = Number(item._sum.currentMonthAmount)
    } else {
      acc.push({
        month: monthKey,
        [item.auditType]: Number(item._sum.currentMonthAmount)
      })
    }
    return acc
  }, [] as any[]).slice(-6) // Only last 6 months

  // Prepare data for audit type bar chart
  const auditTypeData = [
    { auditType: 'SEC', count: anomalyData.stats.byAuditType.find(t => t.auditType === 'SEC')?._count.id || 0 },
    { auditType: 'ACR', count: anomalyData.stats.byAuditType.find(t => t.auditType === 'ACR')?._count.id || 0 },
    { auditType: 'SUB', count: anomalyData.stats.byAuditType.find(t => t.auditType === 'SUB')?._count.id || 0 },
    { auditType: 'ADD', count: anomalyData.stats.byAuditType.find(t => t.auditType === 'ADD')?._count.id || 0 }
  ]

  // Custom Y-axis formatter for commas
  const formatYAxis = (tickItem: number) => {
    return tickItem.toLocaleString()
  }

  const uniqueMonths = getUniqueMonths()

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Alexander Wireless - Telecom Billing Anomaly Detection
          </h1>
          <p className="text-gray-300">
            Real-time insights into billing operations with AI-powered anomaly detection
          </p>
        </div>

        {/* Action Button */}
        {anomalyData.stats.totalAnomalies === 0 && (
          <div className="mb-6">
            <button
              onClick={handleSeedData}
              className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg transition-colors font-semibold"
            >
              Initialize Database with Alexander Wireless Data
            </button>
            <p className="text-sm text-gray-400 mt-2">
              This will populate the database with 6 months of Alexander Wireless billing data and anomalies.
            </p>
          </div>
        )}

        {/* Enhanced Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">
              Total Revenue
            </h3>
            <p className="text-3xl font-bold text-green-400">
              ${anomalyData.billingData.reduce((sum, record) => sum + record.currentMonthAmount, 0).toLocaleString()}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">
              Anomalies Detected
            </h3>
            <p className="text-3xl font-bold text-red-400">
              {anomalyData.stats.totalAnomalies.toLocaleString()}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">
              Critical Issues
            </h3>
            <p className="text-3xl font-bold text-red-400">
              {(anomalyData.stats.bySeverity.find(s => s.severity === 'critical')?._count.id || 0).toLocaleString()}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">
              Processing Cycles
            </h3>
            <p className="text-3xl font-bold text-blue-400">
              {anomalyData.stats.cycles.length.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Dual-Axis Line Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Chart 1: SEC vs ACR */}
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">
              SEC vs ACR - Monthly Totals (Last 6 Months)
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData} margin={{ top: 20, right: 40, left: 40, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9CA3AF" />
                <YAxis yAxisId="left" stroke="#9CA3AF" tickFormatter={formatYAxis} width={80} />
                <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" tickFormatter={formatYAxis} width={80} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                />
                <Legend />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="SEC" 
                  stroke={AUDIT_TYPE_COLORS.SEC} 
                  strokeWidth={3}
                  dot={{ fill: AUDIT_TYPE_COLORS.SEC, strokeWidth: 2, r: 4 }}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="ACR" 
                  stroke={AUDIT_TYPE_COLORS.ACR} 
                  strokeWidth={3}
                  dot={{ fill: AUDIT_TYPE_COLORS.ACR, strokeWidth: 2, r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Chart 2: SUB vs ADD */}
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">
              SUB vs ADD - Monthly Totals (Last 6 Months)
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData} margin={{ top: 20, right: 40, left: 40, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9CA3AF" />
                <YAxis yAxisId="left" stroke="#9CA3AF" tickFormatter={formatYAxis} width={80} />
                <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" tickFormatter={formatYAxis} width={80} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                />
                <Legend />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="SUB" 
                  stroke={AUDIT_TYPE_COLORS.SUB} 
                  strokeWidth={3}
                  dot={{ fill: AUDIT_TYPE_COLORS.SUB, strokeWidth: 2, r: 4 }}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="ADD" 
                  stroke={AUDIT_TYPE_COLORS.ADD} 
                  strokeWidth={3}
                  dot={{ fill: AUDIT_TYPE_COLORS.ADD, strokeWidth: 2, r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Anomaly Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Anomalies by Severity */}
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">
              Anomalies by Severity
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={anomalyData.stats.bySeverity}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ severity, _count }) => 
                    `${severity} (${_count.id.toLocaleString()})`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="_count.id"
                >
                  {anomalyData.stats.bySeverity.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={SEVERITY_COLORS[entry.severity as keyof typeof SEVERITY_COLORS] || '#8884D8'} 
                    />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }}
                  formatter={(value: number) => [value.toLocaleString(), '']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Anomalies by Audit Type */}
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">
              Anomalies by Audit Type
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={auditTypeData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="auditType" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" tickFormatter={formatYAxis} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }}
                  formatter={(value: number) => [value.toLocaleString(), '']}
                />
                <Bar 
                  dataKey="count" 
                  fill="#8B5CF6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Table Filters */}
        <div className="bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-700 mb-6">
          <h3 className="text-xl font-semibold text-white mb-4">
            Table Filters
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Cycle (1-30)
              </label>
              <select
                value={cycleFilter}
                onChange={(e) => setCycleFilter(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">All Cycles</option>
                {Array.from({length: 30}, (_, i) => i + 1).map(num => (
                  <option key={num} value={num.toString().padStart(2, '0')}>
                    {num}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Month
              </label>
              <select
                value={monthFilter}
                onChange={(e) => setMonthFilter(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">All Months</option>
                {uniqueMonths.map(monthKey => {
                  const [year, month] = monthKey.split('-')
                  const monthName = MONTH_NAMES[parseInt(month) - 1]
                  return (
                    <option key={monthKey} value={monthKey}>
                      {monthName} {year}
                    </option>
                  )
                })}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Audit Type
              </label>
              <select
                value={auditTypeFilter}
                onChange={(e) => setAuditTypeFilter(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">All Types</option>
                <option value="SEC">SEC</option>
                <option value="ACR">ACR</option>
                <option value="SUB">SUB</option>
                <option value="ADD">ADD</option>
              </select>
            </div>
          </div>
        </div>

        {/* Detailed Billing Data Table with Research Notes */}
        <div className="bg-gray-800 rounded-lg shadow-lg border border-gray-700">
          <div className="px-6 py-4 border-b border-gray-700">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-semibold text-white">
                Billing Data Analysis
              </h3>
              <div className="text-sm text-gray-300">
                Showing {startIndex + 1}-{Math.min(endIndex, totalRecords)} of {totalRecords.toLocaleString()} records
                {currentRecords.length > 0 && (
                  <span className="ml-4">
                    • {currentRecords.filter(record => record.isAnomaly).length} anomalies on this page
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Cycle
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Billing Code
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Audit Type
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Current Amount
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    5-Month Avg
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    MoM Change
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    MoM %
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Research Notes
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {currentRecords.map((record) => {
                  const alarmWeight = calculateAlarmWeight(record.momChange, record.momChangePercent)
                  const rowColor = getRowColor(alarmWeight, record.isAnomaly)
                  const isEditing = editingNote === record.id
                  
                  return (
                    <tr key={record.id} className={rowColor}>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-800 font-medium">
                        {record.cycle.cycleDate}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-800">
                        {record.billingCode}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-800">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full`}
                              style={{ backgroundColor: `${AUDIT_TYPE_COLORS[record.auditType as keyof typeof AUDIT_TYPE_COLORS]}20`, 
                                       color: AUDIT_TYPE_COLORS[record.auditType as keyof typeof AUDIT_TYPE_COLORS] }}>
                          {record.auditType}
                        </span>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-800">
                        ${record.currentMonthAmount.toLocaleString()}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-800">
                        ${record.rolling5MonthAvg ? record.rolling5MonthAvg.toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-800">
                        <span className={record.momChange >= 0 ? 'text-green-600' : 'text-red-600'}>
                          ${record.momChange.toLocaleString()}
                        </span>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-800">
                        <span className={record.momChangePercent >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {(record.momChangePercent * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        {record.isAnomaly ? (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                            Anomaly
                          </span>
                        ) : (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            Normal
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-800">
                        {record.isAnomaly && record.anomaly && (
                          <div>
                            {/* Show existing notes */}
                            {record.anomaly.analystNotes && record.anomaly.analystNotes.length > 0 && (
                              <div className="mb-2">
                                {record.anomaly.analystNotes.map((note, index) => (
                                  <div key={index} className="text-xs bg-gray-100 p-2 rounded mb-1">
                                    <div className="font-semibold text-gray-700">{note.analystName}</div>
                                    <div className="text-gray-600 text-xs">{note.note}</div>
                                  </div>
                                ))}
                              </div>
                            )}
                            
                            {/* Add new note form */}
                            {isEditing && (
                              <div className="space-y-2">
                                <input
                                  type="text"
                                  placeholder="Analyst name"
                                  value={analystName}
                                  onChange={(e) => setAnalystName(e.target.value)}
                                  className="px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded text-white w-full"
                                />
                                <textarea
                                  placeholder="Note"
                                  value={analystNote}
                                  onChange={(e) => setAnalystNote(e.target.value)}
                                  className="px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded text-white w-full"
                                  rows={2}
                                />
                                <div className="flex space-x-1">
                                  <button
                                    onClick={() => addAnalystNote(record.anomaly!.id)}
                                    disabled={!analystNote.trim() || !analystName.trim() || savingNote === record.anomaly!.id}
                                    data-anomaly-id={record.anomaly!.id}
                                    className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded transition-colors"
                                  >
                                    {savingNote === record.anomaly!.id ? 'Saving...' : 'Save'}
                                  </button>
                                  <button
                                    onClick={() => {
                                      setEditingNote(null)
                                      setAnalystNote('')
                                      setAnalystName('')
                                    }}
                                    className="px-2 py-1 text-xs bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-800">
                        {record.isAnomaly && record.anomaly && (
                          <button
                            onClick={() => setEditingNote(record.id)}
                            className="px-2 py-1 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors"
                          >
                            Edit
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-700">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-300">
                  Showing {startIndex + 1}-{Math.min(endIndex, totalRecords)} of {totalRecords.toLocaleString()} records
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-2 mr-4">
                    <label className="text-sm text-gray-300">Show:</label>
                    <select
                      value={recordsPerPage}
                      onChange={(e) => {
                        setRecordsPerPage(Number(e.target.value))
                        setCurrentPage(1)
                      }}
                      className="px-2 py-1 text-sm bg-gray-700 border border-gray-600 rounded text-white"
                    >
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                      <option value={200}>200</option>
                    </select>
                    <span className="text-sm text-gray-300">records</span>
                  </div>
                  <button
                    onClick={() => setCurrentPage(1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-sm text-gray-300 hover:text-white disabled:text-gray-500 disabled:cursor-not-allowed"
                  >
                    First
                  </button>
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-sm text-gray-300 hover:text-white disabled:text-gray-500 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  {/* Page numbers */}
                  <div className="flex items-center space-x-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum
                      if (totalPages <= 5) {
                        pageNum = i + 1
                      } else if (currentPage <= 3) {
                        pageNum = i + 1
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i
                      } else {
                        pageNum = currentPage - 2 + i
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => setCurrentPage(pageNum)}
                          className={`px-3 py-1 text-sm rounded ${
                            currentPage === pageNum
                              ? 'bg-purple-600 text-white'
                              : 'text-gray-300 hover:text-white hover:bg-gray-700'
                          }`}
                        >
                          {pageNum}
                        </button>
                      )
                    })}
                  </div>
                  
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 text-sm text-gray-300 hover:text-white disabled:text-gray-500 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 text-sm text-gray-300 hover:text-white disabled:text-gray-500 disabled:cursor-not-allowed"
                  >
                    Last
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
