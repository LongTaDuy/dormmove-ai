export interface HealthResponse {
  status: string;
  env: string;
  model_provider: string;
}

// Planned domain types (mirrors backend Pydantic models). Added as the API grows.
// export interface StudentProfile { ... }
// export interface Plan { ... }
// export interface RiskFlag { ... }
