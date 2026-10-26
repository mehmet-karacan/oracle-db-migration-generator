import {Children,isValidElement} from 'react'
import type {ReactElement,ReactNode} from 'react'
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from '@/components/ui/select'

type OptionProps={value:string;children:ReactNode;disabled?:boolean}
type Props={id?:string;value:string;disabled?:boolean;className?:string;'aria-label'?:string;onChange:(value:string)=>void;children:ReactNode}
const emptyValue='__empty_selection__'
export function ChoiceSelect({id,value,disabled,className,onChange,children,'aria-label':label}:Props){
  const options=Children.toArray(children).filter(child=>isValidElement<OptionProps>(child)) as ReactElement<OptionProps>[]
  return <Select value={value||emptyValue} disabled={disabled} onValueChange={next=>onChange(next===emptyValue?'':next)}><SelectTrigger id={id} aria-label={label} className={className}><SelectValue/></SelectTrigger><SelectContent position="popper" align="start" className="choice-menu">{options.map(option=><SelectItem key={option.props.value||emptyValue} value={option.props.value||emptyValue} disabled={option.props.disabled} data-value={option.props.value}>{option.props.children}</SelectItem>)}</SelectContent></Select>
}
