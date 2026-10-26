import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach,expect,it,vi} from 'vitest'
import {PortableCapture} from './PortableCapture'
import {setProjectScope} from './api'

afterEach(()=>vi.unstubAllGlobals())
it('imports a file into the selected project without any password field',async()=>{
  const fetcher=vi.fn(async()=>({ok:true,json:async()=>({id:'imported',capture_schemas:['APP']})}))
  vi.stubGlobal('fetch',fetcher);setProjectScope('project-a')
  const refresh=vi.fn()
  render(<PortableCapture projectId="project-a" refresh={refresh} admin/> )
  await userEvent.type(screen.getByLabelText('Dosya Adı'),'Üretim')
  const file=new File(['synthetic packet'],'capture.odmg.jsonl',{type:'application/octet-stream'})
  await userEvent.upload(screen.getByLabelText('Metadata Dosyası'),file)
  await userEvent.click(screen.getByRole('button',{name:'Dosyayı İçe Aktar'}))
  await waitFor(()=>expect(refresh).toHaveBeenCalled())
  const [url,options]=fetcher.mock.calls[0] as unknown as [string,RequestInit]
  expect(url).toContain('/api/captures/import?name=')
  expect(options.headers).toMatchObject({'X-ODMG-Project':'project-a','Content-Type':'application/octet-stream'})
  expect(options.body).toBe(file)
  expect(screen.queryByLabelText(/Parola/)).not.toBeInTheDocument()
})

it('shares independent filters with table datatype semantics',async()=>{
  render(<PortableCapture projectId="a" refresh={()=>{}} admin/> )
  await userEvent.type(screen.getByLabelText('Şemalar'),'APP, TTBP')
  await userEvent.type(screen.getByLabelText('Nesne Adları'),'ORDERS')
  await userEvent.type(screen.getByLabelText('Kolon Veri Tipleri'),'NUMBER')
  expect(screen.getByText(/Eşleşen nesnenin tüm kolonları/)).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Toplama Paketini İndir'})).toBeEnabled()
})
