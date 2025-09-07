export interface Finding {
  id: string;
  repo_id: string;
  type: 'security' | 'performance' | 'maintainability' | 'style' | 'reliability' | 'architecture';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  file_path?: string;
  start_line?: number;
  end_line?: number;
  start_column?: number;
  end_column?: number;
  created_at: string;
  resolved: boolean;
}

export interface FeatureProposal {
  id: string;
  repo_id: string;
  title: string;
  description: string;
  estimated_effort: 'low' | 'medium' | 'high';
  risk_level: 'low' | 'medium' | 'high';
  created_at: string;
  approved: boolean;
  implemented: boolean;
}

export interface RefactorPlan {
  id: string;
  repo_id: string;
  title: string;
  description: string;
  risk_level: 'low' | 'medium' | 'high';
  estimated_effort: 'low' | 'medium' | 'high';
  created_at: string;
  approved: boolean;
  implemented: boolean;
}

export interface Job {
  id: string;
  job_type: string;
  repo_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  result_data: any;
}

export interface Repository {
  id: string;
  url: string;
  name: string;
  last_analyzed?: string;
  findings_count: number;
  proposals_count: number;
}
