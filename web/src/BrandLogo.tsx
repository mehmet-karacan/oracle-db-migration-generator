import {usePreferences} from './preferences'

export function BrandLogo(){
  const {theme}=usePreferences()
  return <img className="brand-logo" src={theme==='dark'?'/innova-logo-white.svg':'/innova-logo.svg'} alt="İnnova"/>
}
