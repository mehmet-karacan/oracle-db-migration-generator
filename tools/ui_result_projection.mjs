// Self-contained read-only transform, also usable inside the authenticated
// Jenkins JSON document DOM. Only the returned structural view is saved.
export function decodeDocumentText(text,charset) {
  const encoding=charset.toLowerCase()
  if(encoding==='utf-8'||encoding==='utf8')return text
  if(!['windows-1254','windows-1252','iso-8859-1'].includes(encoding))throw new Error('JSON_DOCUMENT_CHARSET_UNSUPPORTED')
  const high=[8364,129,8218,402,8222,8230,8224,8225,710,8240,352,8249,338,141,381,143,144,8216,8217,8220,8221,8226,8211,8212,732,8482,353,8250,339,157,382,376]
  const turkish=encoding==='windows-1254'
  if(turkish){high[14]=142;high[30]=158}
  const specific=turkish?{286:208,304:221,350:222,287:240,305:253,351:254}:{}
  // Recover the exact displayed code-page bytes before JSON.parse. This is
  // transport decoding, never a heuristic substitution in an Oracle value.
  const escaped=text.replace(/[%\u0080-\uffff]/g,ch=>{
    const code=ch.charCodeAt(0),mapped=high.indexOf(code)
    const byte=ch==='%'?37:mapped>=0?mapped+128:specific[code]??(code>=160&&code<=255?code:256)
    if(byte>255)throw new Error('JSON_DOCUMENT_BYTE_RECOVERY_FAILED')
    return '%'+byte.toString(16).padStart(2,'0')
  })
  return decodeURIComponent(escaped)
}

// Canonical Generator JSON emits Unicode as UTF-8, not ASCII escapes.
// Decode strings after the DOM projection when a restricted browser bridge
// does not expose TextDecoder/URI decoding. Raw definitions remain in the DOM.
export function decodeProjectedView(view,charset) {
  if(typeof view==='string')return decodeDocumentText(view,charset)
  if(Array.isArray(view))return view.map(v=>decodeProjectedView(v,charset))
  if(view!==null&&typeof view==='object')return Object.fromEntries(Object.entries(view).map(([key,value])=>[decodeDocumentText(key,charset),decodeProjectedView(value,charset)]))
  return view
}

export function projectPlan(plan) {
  function metadataPath(path) {
    const parts=path.replace(/^\/+|\/+$/g,'').split('/')
    return ['columns','constraints','index','sequence','table_properties','trigger','editionable','presence','coverage'].includes(parts[0]) && !parts.some(p=>['definition','structured','ddl','sql','body','statement'].includes(p))
  }
  function value(path,item) {
    const omitted=!metadataPath(path)||JSON.stringify(item.value).length>32768
    return {state:item.state,value:omitted||item.state!=='KNOWN'?null:item.value,omitted}
  }
  return {
    schema_version:'comparison-view/1.0',plan_id:plan.plan_id,source_commit:plan.source.commit_sha,
    target_id:plan.target.id,synthetic:plan.synthetic,scope:plan.scope,counts:plan.counts,
    differences:plan.differences.map(row=>{
      const path=row.property_path.startsWith('/')?row.property_path:'/'+row.property_path.replaceAll('.','/')
      return {id:row.id,object_key:row.object_key,property_path:path,kind:row.kind,
        source:value(path,row.after),target:value(path,row.before),evidence_ids:row.evidence_ids}
    }),
    operations:plan.operations.map(op=>({id:op.id,object:op.object,kind:op.kind,decision:op.decision,
      reason_tr:op.reason_tr,change_ids:op.change_ids,evidence_ids:op.evidence_ids||[],depends_on:op.depends_on||[],sql_path:op.sql?.path||null})),
  }
}
