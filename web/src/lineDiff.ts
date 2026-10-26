export type CodeLine={number:number;text:string}
export type AlignedLine={source:CodeLine|null;target:CodeLine|null;kind:'equal'|'changed'|'source_only'|'target_only'}
export function alignLines(source:string,target:string):{rows:AlignedLine[];coarse:boolean}{
 const a=source.split('\n'),b=target.split('\n'),rows:AlignedLine[]=[]
 let start=0,endA=a.length,endB=b.length
 while(start<endA&&start<endB&&a[start]===b[start]){rows.push({source:{number:start+1,text:a[start]},target:{number:start+1,text:b[start]},kind:'equal'});start++}
 while(endA>start&&endB>start&&a[endA-1]===b[endB-1]){endA--;endB--}
 const n=endA-start,m=endB-start,coarse=n*m>250000
 let sourceBlock:CodeLine[]=[],targetBlock:CodeLine[]=[]
 function flush(){for(let k=0;k<Math.max(sourceBlock.length,targetBlock.length);k++){const left=sourceBlock[k]||null,right=targetBlock[k]||null;rows.push({source:left,target:right,kind:left&&right?'changed':left?'source_only':'target_only'})}sourceBlock=[];targetBlock=[]}
 if(coarse){sourceBlock=a.slice(start,endA).map((text,i)=>({number:start+i+1,text}));targetBlock=b.slice(start,endB).map((text,i)=>({number:start+i+1,text}));flush()}
 else{
  const lengths=Array.from({length:n+1},()=>new Uint32Array(m+1))
  for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)lengths[i][j]=a[start+i]===b[start+j]?lengths[i+1][j+1]+1:Math.max(lengths[i+1][j],lengths[i][j+1])
  let i=0,j=0
  while(i<n||j<m){
   if(i<n&&j<m&&a[start+i]===b[start+j]){flush();rows.push({source:{number:start+i+1,text:a[start+i]},target:{number:start+j+1,text:b[start+j]},kind:'equal'});i++;j++}
   else if(i<n&&(j>=m||lengths[i+1][j]>=lengths[i][j+1])){sourceBlock.push({number:start+i+1,text:a[start+i]});i++}
   else{targetBlock.push({number:start+j+1,text:b[start+j]});j++}
  }
  flush()
 }
 while(endA<a.length&&endB<b.length){rows.push({source:{number:endA+1,text:a[endA]},target:{number:endB+1,text:b[endB]},kind:'equal'});endA++;endB++}
 return {rows,coarse}
}
