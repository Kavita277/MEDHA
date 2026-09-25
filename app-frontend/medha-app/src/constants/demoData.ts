/**
 * MEDHA Frontend Demo Data Layer
 * ==============================
 * Clearly isolated, non-clinical mock datasets for demonstration, offline preview,
 * and role-based workflows (Guardian, Therapist Workspace, and Admin Dashboard).
 *
 * NOTE: This data is for frontend demonstration and operational layout testing only.
 * It is NOT real patient health data and MUST NOT be represented as clinical diagnosis.
 */

export interface GuardianData {
  guardianName: string;
  linkedPatient: {
    name: string;
    patientId: string;
    wellbeingStatus: string;
    wellbeingLevel: 'gentle' | 'moderate' | 'needs_attention';
    recentCheckInTime: string;
    checkInStep: string;
    streakDays: number;
    lastActivity: string;
  };
  wellbeingSummary: {
    moodTrendText: string;
    moodTrendDirection: 'steady' | 'improving' | 'declining';
    checkInConsistencyPct: number;
    recentSupportActivity: string;
  };
  careProfessional: {
    name: string;
    title: string;
    clinic: string;
    phone: string;
  };
}

export const GUARDIAN_DEMO_DATA: GuardianData = {
  guardianName: 'Sunita Sharma',
  linkedPatient: {
    name: 'Aarav Sharma',
    patientId: 'PT-8802',
    wellbeingStatus: 'Gentle & Steady · Within Normal Baseline',
    wellbeingLevel: 'gentle',
    recentCheckInTime: 'Today at 10:15 AM',
    checkInStep: 'Step 2 of 2 completed',
    streakDays: 4,
    lastActivity: 'Listened to 5-min Grounding Audio',
  },
  wellbeingSummary: {
    moodTrendText: 'Gentle and consistent over the past 7 days',
    moodTrendDirection: 'steady',
    checkInConsistencyPct: 86,
    recentSupportActivity: 'Viewed self-care resource: Breathing Space',
  },
  careProfessional: {
    name: 'Dr. Ananya Roy',
    title: 'Licensed Clinical Psychologist',
    clinic: 'MindCare Clinic, New Delhi',
    phone: '+91 98765 01234',
  },
};

export interface TherapistCaseSummary {
  caseId: string;
  patientId: string;
  patientName: string;
  wellbeingStatus: string;
  riskLevel: 'Low' | 'Moderate' | 'Needs Attention';
  trend: 'Improving' | 'Stable' | 'Increasing';
  lastInteraction: string;
  alertActive: boolean;
  alertTitle?: string;
}

export const THERAPIST_DEMO_CASES: TherapistCaseSummary[] = [
  {
    caseId: 'CASE-9021',
    patientId: 'PT-8802',
    patientName: 'Aarav S.',
    wellbeingStatus: 'Elevated tension reported',
    riskLevel: 'Needs Attention',
    trend: 'Increasing',
    lastInteraction: '2 hours ago (Check-in + Voice note)',
    alertActive: true,
    alertTitle: 'Human review recommended',
  },
  {
    caseId: 'CASE-8412',
    patientId: 'PT-7640',
    patientName: 'Priya M.',
    wellbeingStatus: 'Calm & stable trajectory',
    riskLevel: 'Low',
    trend: 'Stable',
    lastInteraction: 'Yesterday (Evening Journal)',
    alertActive: false,
  },
  {
    caseId: 'CASE-7105',
    patientId: 'PT-5129',
    patientName: 'Rohan K.',
    wellbeingStatus: 'Positive response to grounding',
    riskLevel: 'Low',
    trend: 'Improving',
    lastInteraction: '3 days ago (Grounding session)',
    alertActive: false,
  },
  {
    caseId: 'CASE-6230',
    patientId: 'PT-9931',
    patientName: 'Neha V.',
    wellbeingStatus: 'Fluctuating sleep & restlessness',
    riskLevel: 'Needs Attention',
    trend: 'Increasing',
    lastInteraction: '4 hours ago (Voice check-in)',
    alertActive: true,
    alertTitle: 'Sleep pattern disruption',
  },
  {
    caseId: 'CASE-5541',
    patientId: 'PT-3418',
    patientName: 'Ananya D.',
    wellbeingStatus: 'Steady engagement pattern',
    riskLevel: 'Low',
    trend: 'Stable',
    lastInteraction: '2 days ago (Check-in completed)',
    alertActive: false,
  },
];

export interface TherapistCaseDetail {
  caseId: string;
  patientId: string;
  patientName: string;
  status: string;
  riskLevel: 'Low' | 'Moderate' | 'Needs Attention';
  trend: 'Improving' | 'Stable' | 'Increasing';
  lastCheckIn: string;
  lastInteraction: string;
  explainability: {
    headline: string;
    factors: {
      id: string;
      title: string;
      description: string;
      type: 'Text' | 'Voice' | 'Behaviour' | 'Pattern' | 'Safety';
      severity: 'neutral' | 'notice' | 'attention';
    }[];
  };
  temporalTrend: {
    direction: 'Improving' | 'Stable' | 'Increasing';
    changeFromBaseline: string;
    points: { day: string; value: number }[];
  };
  modalitySignals: {
    textDistress: { value: number | null; label: string; interpretation: string };
    voiceDistress: { value: number | null; label: string; interpretation: string };
    behaviouralRisk: { value: number | null; label: string; interpretation: string };
    structuredIntake: { value: number | null; label: string; interpretation: string };
    temporalRisk: { value: number | null; label: string; interpretation: string };
  };
  safetyAlert: {
    active: boolean;
    title: string;
    description: string;
    humanReviewRecommended: boolean;
    protocolSummary: string;
  };
  recommendations: {
    id: string;
    category: string;
    title: string;
    description: string;
    actionLabel: string;
  }[];
  recentInteractions: {
    id: string;
    type: 'Check-in' | 'Voice Note' | 'Journal' | 'Grounding' | 'Support';
    timestamp: string;
    summary: string;
    badgeBg: string;
    badgeColor: string;
  }[];
}

export const THERAPIST_DEMO_CASE_DETAILS: Record<string, TherapistCaseDetail> = {
  'CASE-9021': {
    caseId: 'CASE-9021',
    patientId: 'PT-8802',
    patientName: 'Aarav S.',
    status: 'Clinical Review Flagged',
    riskLevel: 'Needs Attention',
    trend: 'Increasing',
    lastCheckIn: 'Today at 10:15 AM (Step 2/2)',
    lastInteraction: 'Voice note (45s) & Check-in',
    explainability: {
      headline: 'Why this case needs clinical review',
      factors: [
        {
          id: 'f1',
          title: 'Recent self-reported distress rise',
          description: 'Check-in responses over the past 48 hours show increased self-reported tension and difficulty resting.',
          type: 'Text',
          severity: 'attention',
        },
        {
          id: 'f2',
          title: 'Voice acoustic variation',
          description: 'Acoustic pitch variability and speech pause rate deviate +22% from patient personal 14-day baseline.',
          type: 'Voice',
          severity: 'attention',
        },
        {
          id: 'f3',
          title: 'Shift in interaction timing',
          description: 'App check-in shifted from regular morning hours to late-night hours over 3 consecutive nights.',
          type: 'Behaviour',
          severity: 'notice',
        },
        {
          id: 'f4',
          title: 'Safety context review',
          description: 'No imminent crisis triggers detected. Flagged for clinician follow-up due to co-occurring sleep deficit.',
          type: 'Safety',
          severity: 'notice',
        },
      ],
    },
    temporalTrend: {
      direction: 'Increasing',
      changeFromBaseline: '+18% above 14-day personal baseline',
      points: [
        { day: 'Mon', value: 34 },
        { day: 'Tue', value: 36 },
        { day: 'Wed', value: 42 },
        { day: 'Thu', value: 50 },
        { day: 'Fri', value: 62 },
        { day: 'Sat', value: 68 },
        { day: 'Sun', value: 65 },
      ],
    },
    modalitySignals: {
      textDistress: {
        value: 68,
        label: '68 / 100',
        interpretation: 'Elevated tension keywords observed in optional check-in response.',
      },
      voiceDistress: {
        value: 64,
        label: '64 / 100',
        interpretation: 'Higher vocal strain index and prolonged hesitation markers.',
      },
      behaviouralRisk: {
        value: 52,
        label: '52 / 100',
        interpretation: 'Irregular check-in times; missed morning reflection routine.',
      },
      structuredIntake: {
        value: 70,
        label: '70 / 100',
        interpretation: 'Self-reported feeling overwhelmed and restless.',
      },
      temporalRisk: {
        value: 60,
        label: '60 / 100',
        interpretation: 'Upward 4-day trajectory across multiple modalities.',
      },
    },
    safetyAlert: {
      active: true,
      title: 'Active Safety Review Flag',
      description: 'Elevated distress indicators co-occurring with sleep disruption. Immediate human review recommended. No explicit crisis language identified.',
      humanReviewRecommended: true,
      protocolSummary: 'Therapist clinical review recommended before next scheduled consultation.',
    },
    recommendations: [
      {
        id: 'r1',
        category: 'Clinical Follow-up',
        title: 'Review recent check-in & audio recording',
        description: 'Listen to the 45-second patient voice check-in from 10:18 AM to assess subjective state.',
        actionLabel: 'Review Note',
      },
      {
        id: 'r2',
        category: 'Care Consultation',
        title: 'Schedule a 15-minute supportive check-in',
        description: 'Offer a brief check-in session focusing on sleep hygiene and stress management.',
        actionLabel: 'Schedule Call',
      },
      {
        id: 'r3',
        category: 'Psychoeducation',
        title: 'Suggest grounding & breathwork module',
        description: 'Recommend the 4-7-8 breathing exercise in the patient self-help library.',
        actionLabel: 'Share Module',
      },
    ],
    recentInteractions: [
      {
        id: 'i1',
        type: 'Check-in',
        timestamp: 'Today, 10:15 AM',
        summary: 'Step 2 completed: "Feeling very overwhelmed with upcoming deadlines and trouble sleeping"',
        badgeBg: '#FFEADB',
        badgeColor: '#E8663F',
      },
      {
        id: 'i2',
        type: 'Voice Note',
        timestamp: 'Today, 10:18 AM',
        summary: 'Recorded 45-second voice reflection regarding exhaustion and work stress',
        badgeBg: '#E1F2FE',
        badgeColor: '#0284C7',
      },
      {
        id: 'i3',
        type: 'Journal',
        timestamp: 'Yesterday, 9:30 PM',
        summary: 'Private journal reflection logged: 124 words on restlessness',
        badgeBg: '#EEE9FA',
        badgeColor: '#7C6EE6',
      },
      {
        id: 'i4',
        type: 'Grounding',
        timestamp: '2 days ago, 4:20 PM',
        summary: 'Completed 5-minute Box Breathing exercise in Find Your Center',
        badgeBg: '#E2F5E8',
        badgeColor: '#2D8A4E',
      },
    ],
  },
};

export interface AdminData {
  overview: {
    totalPatients: number;
    activeCases: number;
    activeTherapists: number;
    openAlerts: number;
  };
  systemStatus: {
    backend: { status: 'healthy' | 'degraded'; uptime: string; latency: string };
    aiPipeline: { status: 'healthy' | 'degraded'; uptime: string; latency: string };
    notifications: { status: 'healthy' | 'degraded'; activeWorkers: number };
    deviceGateway: { status: 'healthy' | 'degraded'; connectedDevices: number };
  };
  patients: {
    id: string;
    name: string;
    enrolledDate: string;
    status: 'Active' | 'Under Review' | 'Archived';
    assignedTherapist: string;
    lastActivity: string;
  }[];
  therapists: {
    id: string;
    name: string;
    license: string;
    activeCases: number;
    status: 'Verified' | 'Pending Review';
  }[];
  cases: {
    id: string;
    patientId: string;
    patientName: string;
    therapistName: string;
    priority: 'Normal' | 'High' | 'Immediate Review';
    openedDate: string;
    status: 'Open' | 'Monitoring' | 'Resolved';
  }[];
  alerts: {
    id: string;
    caseId: string;
    severity: 'High' | 'Medium' | 'Low';
    title: string;
    timestamp: string;
    status: 'Pending Review' | 'Acknowledged';
  }[];
  auditLogs: {
    id: string;
    timestamp: string;
    actor: string;
    role: string;
    action: string;
    resource: string;
    status: 'SUCCESS' | 'DENIED';
  }[];
}

export const ADMIN_DEMO_DATA: AdminData = {
  overview: {
    totalPatients: 148,
    activeCases: 42,
    activeTherapists: 12,
    openAlerts: 3,
  },
  systemStatus: {
    backend: {
      status: 'healthy',
      uptime: '99.98%',
      latency: '42ms',
    },
    aiPipeline: {
      status: 'healthy',
      uptime: '99.94%',
      latency: '240ms',
    },
    notifications: {
      status: 'healthy',
      activeWorkers: 4,
    },
    deviceGateway: {
      status: 'healthy',
      connectedDevices: 89,
    },
  },
  patients: [
    { id: 'PT-8802', name: 'Aarav Sharma', enrolledDate: '12 Aug 2026', status: 'Under Review', assignedTherapist: 'Dr. Ananya Roy', lastActivity: '2 hours ago' },
    { id: 'PT-7640', name: 'Priya Mukherjee', enrolledDate: '01 Jul 2026', status: 'Active', assignedTherapist: 'Dr. Vikram Seth', lastActivity: 'Yesterday' },
    { id: 'PT-5129', name: 'Rohan Kapoor', enrolledDate: '18 Jun 2026', status: 'Active', assignedTherapist: 'Dr. Ananya Roy', lastActivity: '3 days ago' },
    { id: 'PT-9931', name: 'Neha Varma', enrolledDate: '24 Jul 2026', status: 'Under Review', assignedTherapist: 'Dr. Meera Nambiar', lastActivity: '4 hours ago' },
    { id: 'PT-3418', name: 'Ananya Deshmukh', enrolledDate: '05 May 2026', status: 'Active', assignedTherapist: 'Dr. Vikram Seth', lastActivity: '2 days ago' },
  ],
  therapists: [
    { id: 'TH-101', name: 'Dr. Ananya Roy', license: 'RCI-CLIN-2022-89', activeCases: 8, status: 'Verified' },
    { id: 'TH-102', name: 'Dr. Vikram Seth', license: 'RCI-CLIN-2020-41', activeCases: 14, status: 'Verified' },
    { id: 'TH-103', name: 'Dr. Meera Nambiar', license: 'RCI-CLIN-2023-11', activeCases: 9, status: 'Verified' },
    { id: 'TH-104', name: 'Dr. Siddharth Rao', license: 'RCI-CLIN-2021-95', activeCases: 11, status: 'Verified' },
  ],
  cases: [
    { id: 'CASE-9021', patientId: 'PT-8802', patientName: 'Aarav Sharma', therapistName: 'Dr. Ananya Roy', priority: 'Immediate Review', openedDate: '15 Aug 2026', status: 'Monitoring' },
    { id: 'CASE-8412', patientId: 'PT-7640', patientName: 'Priya Mukherjee', therapistName: 'Dr. Vikram Seth', priority: 'Normal', openedDate: '10 Jul 2026', status: 'Open' },
    { id: 'CASE-7105', patientId: 'PT-5129', patientName: 'Rohan Kapoor', therapistName: 'Dr. Ananya Roy', priority: 'Normal', openedDate: '22 Jun 2026', status: 'Open' },
    { id: 'CASE-6230', patientId: 'PT-9931', patientName: 'Neha Varma', therapistName: 'Dr. Meera Nambiar', priority: 'High', openedDate: '01 Aug 2026', status: 'Monitoring' },
  ],
  alerts: [
    { id: 'ALT-401', caseId: 'CASE-9021', severity: 'High', title: 'Multimodal distress indicator elevation', timestamp: 'Today, 10:20 AM', status: 'Pending Review' },
    { id: 'ALT-398', caseId: 'CASE-6230', severity: 'Medium', title: 'Prolonged sleep disruption observed', timestamp: 'Today, 06:14 AM', status: 'Pending Review' },
    { id: 'ALT-385', caseId: 'CASE-8412', severity: 'Low', title: 'Missed scheduled check-in window', timestamp: 'Yesterday, 08:00 PM', status: 'Acknowledged' },
  ],
  auditLogs: [
    { id: 'AUD-901', timestamp: '2026-09-25 18:45:10', actor: 'th_ananya_roy', role: 'Therapist', action: 'THERAPIST_VIEWED_INSIGHTS', resource: 'CASE-9021', status: 'SUCCESS' },
    { id: 'AUD-900', timestamp: '2026-09-25 18:30:22', actor: 'admin_ops', role: 'Admin', action: 'ADMIN_CHECKED_SYSTEM_HEALTH', resource: 'SYSTEM_CLUSTER', status: 'SUCCESS' },
    { id: 'AUD-899', timestamp: '2026-09-25 17:12:04', actor: 'th_ananya_roy', role: 'Therapist', action: 'CASE_NOTE_ADDED', resource: 'CASE-9021', status: 'SUCCESS' },
    { id: 'AUD-898', timestamp: '2026-09-25 15:05:44', actor: 'unauth_req', role: 'Unknown', action: 'ACCESS_ATTEMPT', resource: 'CASE-8412', status: 'DENIED' },
  ],
};
