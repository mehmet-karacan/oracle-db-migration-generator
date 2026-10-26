import {translate as t} from './preferences'
export type Connection = {
  project_id?: string;
  id: string; revision: number; updated_at: string; name: string; kind: 'GIT' | 'ORACLE' | 'SNAPSHOT';
  capture_id?:string; capture_schemas?:string[];
  capture_summary?:{sha256:string;captured_at:string;environment?:string;status:string;inventory_complete:boolean;selected_objects:number;filter:CaptureFilter};
  host?: string; port: number; service_name?: string; sid?: string; repository?: string;
  driver_mode: 'thin' | 'thick'; metadata_reader?: string; allowed_users: string[]; credential_configured: boolean;
}
export type SchemaPair = { source_schema:string; target_schema:string }
export type SchemaMapping = {
  id:string; revision:number; name:string; project_id?:string;
  source:{kind:'GIT'|'ORACLE'|'SNAPSHOT';connection_id:string;schemas:string[]};
  target_ids:string[];target_mappings:Record<string,SchemaPair[]>;
}
export type Profile = {
  project_id?: string;
  id: string; revision: number; updated_at: string; name: string;
  source: { kind: 'GIT' | 'ORACLE' | 'SNAPSHOT'; connection_id: string; schemas: string[]; ref: string; layout: 'by_object' | 'flat'; roots: Record<string,string> };
  capture_filter?:CaptureFilter|null;
  target_ids: string[]; object_types: string[]; excluded_object_types: string[];
  target_mappings?: Record<string,SchemaPair[]> | null;
  mapping_id?:string|null; mapping_revision?:number|null;
  exclude_system_generated: boolean; compare_physical_storage: boolean; source_length_semantics: string;
}
export type Settings = Record<string, string | number | boolean>
export type CaptureFilter={schemas?:string[];object_types?:string[];object_names?:string[];data_types?:string[];include_related?:boolean;exclude_system_generated?:boolean;environment?:string;reader_mode?:string;filter_side?:'SOURCE'|'TARGET';timeout_seconds?:number;max_objects?:number}
export type Project = { id:string; revision:number; name:string; code:string }
export type Session = { local_execution_available?:boolean; user: string; display_name?:string; role: 'admin' | 'operator' | 'viewer' | 'shared'; mode: string; artifact_mode: string; executor_configured: boolean }
export type Run = {
  executor?:string; artifact_mode?:string; archive_build_url?:string;
  external?: { mode:string; launch_url:string; schema_scope:string; target_map?:Record<string,string>; build_url?:string; report_url?:string; verification?:string; build_number?:number };
  project_id?: string; project_name?: string; profile_name?: string;
  id: string; actor: string; status: string; stage: string; created_at: string; started_at?: string; finished_at?: string;
  error_code?: string; report_available?: boolean; settings_fingerprint: string;
  targets: { id: string; status: string; plan_id?: string; difference_count: number | null; error_code?: string }[];
  progress?: { processed?: number; total?: number; target_id?: string };
  events?: { stage: string; at: string }[];
  spec?: { profile: Profile; settings: Settings; connections: Record<string, Connection> };
  source_performance?: { seconds: number; cache_status: string; source_kind: string };
}
export type Operation = { id: string; object: { owner: string; name: string; object_type: string }; decision: string; kind: string; reason_tr: string; reason_codes: string[]; evidence_ids: string[]; sql?: { path: string } }
export type OperationPage = { rows: Operation[]; total: number | null; plan_available: boolean; counts?: Record<string,number> }

const errors: Record<string,string> = {
  CAPTURE_REQUIRES_LOCAL_EXECUTOR:'Dosyadan karşılaştırma için Bu Bilgisayar seçeneğini kullanın.',
  CAPTURE_SCHEMA_NOT_EXPORTED:'Seçilen şema bu dosyada bulunmuyor.',
  CAPTURE_UI_SCHEMA_UNSUPPORTED:'Bu dosyadaki şema adları mevcut eşleştirme biçimiyle uyumlu değil. CLI içe aktarmayı kullanın.',
  CAPTURE_INTEGRITY:'Metadata dosyası değişmiş. Dosyayı yeniden içe aktarın.',
  LOCAL_EXECUTOR_UNAVAILABLE:'Yerel çalıştırıcı bu sunucuda kullanılamıyor.',
  EXECUTOR_INVALID:'Çalıştırma yeri geçersiz.',
  LOGIN_INVALID:'Kullanıcı adı veya parola hatalı.',
  LOGIN_RATE_LIMIT:'Çok fazla giriş denemesi yapıldı. 15 dakika sonra tekrar deneyin.',
  PASSWORD_LENGTH_INVALID:'Parola 12 ile 256 karakter arasında olmalı.',
  ACCOUNT_ALREADY_CONFIGURED:'Hesap zaten hazır. Giriş ekranını kullanın.',
  SETUP_LOOPBACK_ONLY:'İlk parola kurulumu sunucunun yerel adresinden yapılmalı.',
  PROJECT_SCOPE_MISMATCH:'Bu kayıt seçili projeye ait değil. Projeyi ve seçiminizi kontrol edin.',
  RECORD_NOT_FOUND:'Bu projede kayıt bulunamadı.',
  TARGET_SCHEMA_SCOPE_REQUIRED: 'Her hedef için karşılaştırılacak şema eşleştirmesini seçin.',
  CATALOG_READER_ROLE_REQUIRED: 'Bağlantı hesabının başka bir şemayı tam okumak için gereken SELECT_CATALOG_ROLE yetkisi yok.',
  CATALOG_READER_OWNER_UNVERIFIED: 'Seçilen şemanın varlığı doğrulanamadı. Şema adını ve katalog erişimini kontrol edin.',
  CONFIGURATION_INVALID: 'Bilgiler geçersiz. Bağlantı, şema ve süre alanlarını kontrol edin.',
  REVISION_CONFLICT: 'Bu kayıt başka bir kullanıcı tarafından değiştirildi. Güncelleyip tekrar deneyin.',
  IDENTITY_REQUIRED: 'Kurumsal oturum doğrulanamadı. Uygulamaya yetkili giriş adresinden erişin.',
  ACCESS_FORBIDDEN: 'Bu bağlantıyı veya işlemi kullanma yetkiniz yok.', ADMIN_REQUIRED: 'Bu işlem yönetici yetkisi gerektirir.',
  JENKINS_EXECUTOR_NOT_CONFIGURED: 'Ortak çalıştırıcı henüz yapılandırılmadı. Jenkins entegrasyonu yönetici tarafından tamamlanmalı.',
  JENKINS_PROFILE_NOT_CONFIGURED: 'Bu seçim mevcut Jenkins işiyle eşleşmiyor. Kayıtlı canlı profili seçin. Değiştirilen kapsam için çalıştırıcı eşlemesi gerekiyor.',
  GIT_ACCESS_FAILED: 'Git deposuna erişilemedi. Adresi, erişim bilgilerini ve servis durumunu kontrol edin.',
  SESSION_OWNER_MISMATCH: 'Bağlantı kullanıcısı ile seçili şema farklı. Yetkili katalog okuyucusu tanımı gerekiyor.',
  GIT_REF_AMBIGUOUS: 'Aynı isimde branch ve tag var. refs/tags/... veya refs/remotes/origin/... ile açık seçim yapın.',
  GIT_REF_NOT_FOUND: 'Seçilen branch, tag veya commit depoda bulunamadı.',
  MIXED_ORACLE_DRIVER_MODES: 'Aynı karşılaştırmadaki Oracle bağlantıları aynı Thin/Thick modunu kullanmalı.',
  ORACLE_CLIENT_REQUIRED: 'Thick bağlantı için sunucuda Oracle istemci dizini tanımlanmalı.',
  SOURCE_CAPTURE_ERROR: 'Kaynak Oracle bilgileri alınamadı. Bağlantıyı ve metadata erişimini kontrol edin.',
  SOURCE_CAPTURE_INCONSISTENT: 'Kaynak okunurken nesneler değişti. Tutarlı kaynak yakalanamadı. Karşılaştırmayı yeniden başlatın.',
  WORKER_INTERRUPTED: 'Çalıştırıcı süreç kesildi. Bu çalışmadan tam sonuç alınamadı.',
  JOB_TIMEOUT: 'Çalışma için tanımlanan süre sınırı aşıldı.',
}
export function errorText(code: string) { return t(errors[code] || (code.startsWith('CAPTURE_')?t('Metadata dosyası veya toplama parametreleri doğrulanamadı ({0}).',{0:code}):t('İşlem tamamlanamadı ({0}).',{0:code}))) }
let activeProject=''
export function projectHeaders():Record<string,string>{return activeProject?{'X-ODMG-Project':activeProject}:{}}
export function setProjectScope(id:string){activeProject=id}
export async function captureRequest(path:string,body:BodyInit,contentType:string,projectId:string){
  const response=await fetch('/api/captures/'+path,{method:'POST',headers:{'X-ODMG-Project':projectId,'Content-Type':contentType},body})
  if(!response.ok){
    if(response.status===401)window.dispatchEvent(new Event('odmg-session-expired'))
    const data=await response.json();throw new Error(errorText(data.detail||'CAPTURE_INVALID'))
  }
  return response
}
export async function api<T>(path: string, body?: unknown, method = 'POST'): Promise<T> {
  let response: Response
  const scoped=!/^\/(auth(?:\/|$)|session(?:\?|$)|projects(?:\?|$))/.test(path)
  const explicit=new URLSearchParams(path.split('?')[1]||'').get('project_id')
  const project=explicit||activeProject
  const headers:Record<string,string>=scoped&&project?{'X-ODMG-Project':project}:{}
  try { response = await fetch(`/api${path}`, body === undefined ? (Object.keys(headers).length?{headers}:{}) : { method, headers: { ...headers,'Content-Type': 'application/json' }, body: JSON.stringify(body) }) }
  catch { throw new Error(t('Sunucuya ulaşılamadı. Bağlantıyı kontrol edin.')) }
  const data = await response.json()
  if (!response.ok) {
    if(response.status===401&&!path.startsWith('/auth/'))window.dispatchEvent(new Event('odmg-session-expired'))
    throw new Error(errorText(data.error_code || data.detail || `HTTP_${response.status}`))
  }
  return data as T
}
export const artifactUrl = (run: string, path: string) => `/api/runs/${run}/artifacts/${path.split('/').map(encodeURIComponent).join('/')}${activeProject?'?project_id='+encodeURIComponent(activeProject):''}`
export const statusLabel = (status: string) => t({ AWAITING_JENKINS: 'Jenkins sonucu bekleniyor', COMPLETE: 'Tamamlandı', PARTIAL: 'Kısmen Tamamlandı', FAILED: 'Başarısız', RUNNING: 'Çalışıyor', QUEUED: 'Sırada', READY: 'DDL hazır', REVIEW_REQUIRED: 'İnceleme gerekli', BLOCKED: 'DDL üretilemedi', INFORMATIONAL: 'Bilgi', INCONSISTENT: 'Yakalama sırasında değişti', ERROR: 'Sonuç alınamadı', NO_CHANGE: 'Fark yok', NO_ACTION: 'İşlem gerekmiyor' }[status] || status)
export const stageLabel = (stage: string) => t({ SOURCE_IMPORT: 'Kaynak dosyası okunuyor', TARGET_IMPORT: 'Hedef dosyası okunuyor', JENKINS_HANDOFF: 'Jenkins oturumuna aktarım', QUEUED: 'Sıraya alındı', SOURCE: 'Kaynak hazırlanıyor', GIT_FETCH: 'Git kaynağı alınıyor', SOURCE_PARSE: 'Kaynak çözümleniyor', SOURCE_CAPTURE: 'Kaynak Oracle okunuyor', TARGET_CAPTURE: 'Hedef karşılaştırılıyor', REPORT: 'Rapor hazırlanıyor', FINISHED: 'İşlem Bitti', FAILED: 'İşlem durdu' }[stage] || stage)
export function duration(start?: string, end?: string) { if (!start) return t('Bekleniyor'); const s = Math.max(0, Math.round(((end ? Date.parse(end) : Date.now()) - Date.parse(start)) / 1000)); return t('{0} dk {1} sn',{0:Math.floor(s/60),1:s%60}) }
export const objectTypes = ['TABLE','VIEW','MATERIALIZED_VIEW','INDEX','SEQUENCE','FUNCTION','PROCEDURE','PACKAGE_SPEC','PACKAGE_BODY','TYPE_SPEC','TYPE_BODY','TRIGGER','SYNONYM','COMMENT','GRANT','MATERIALIZED_VIEW_LOG']
export const typeLabel = (kind: string) => t({ TABLE:'Tablo', VIEW:'Görünüm', MATERIALIZED_VIEW:'Saklanan görünüm', INDEX:'İndeks', SEQUENCE:'Sıra numarası', FUNCTION:'Fonksiyon', PROCEDURE:'Prosedür', PACKAGE_SPEC:'Paket tanımı', PACKAGE_BODY:'Paket gövdesi', TYPE_SPEC:'Veri tipi', TYPE_BODY:'Tip gövdesi', TRIGGER:'Tetikleyici', SYNONYM:'Eş ad', COMMENT:'Açıklama', GRANT:'Yetki', MATERIALIZED_VIEW_LOG:'Saklanan görünüm günlüğü' }[kind] || kind)

export const filterValues=(value:string)=>value.split(',').map(s=>s.trim()).filter(Boolean)
