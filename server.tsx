import { Hono } from 'hono'
import { serveStatic } from 'hono/bun'
import { RegistreContabile } from './src/pages/RegistreContabile'
import { CreeazaFactura } from './src/pages/CreeazaFactura'
import { AdaugaCheltuieli } from './src/pages/AdaugaCheltuieli'
import { AdaugaIncasari } from './src/pages/AdaugaIncasari'
import { AdaugaDeclaratii } from './src/pages/AdaugaDeclaratii'
import { ObiecteDeInventar } from './src/pages/ObiecteDeInventar'
import { CreeazaDeclaratii } from './src/pages/CreeazaDeclaratii'
import { SetariAplicatie } from './src/pages/SetariAplicatie'
import { SetariPragMijlocFix } from './src/pages/SetariPragMijlocFix'


// Embed static files in binary
// @ts-ignore
import css from "./static/output.css" with { type: "file" } 



const app = new Hono()

app.use('/static/*', serveStatic({ root: `./` }))


app.get('/', (c) => {
  return c.html(<RegistreContabile />)
})

app.get('/registre-contabile', (c) => {
  return c.html(<RegistreContabile />)
})

app.get('/creeaza-factura', (c) => {
  return c.html(<CreeazaFactura />)
})

app.get('/adauga-incasari', (c) => {
  return c.html(<AdaugaIncasari />)
})

app.get('/adauga-cheltuieli', (c) => {
  return c.html(<AdaugaCheltuieli />)
})

app.get('/adauga-declaratii', (c) => {
  return c.html(<AdaugaDeclaratii />)
})

app.get('/obiecte-de-inventar', (c) => {
  return c.html(<ObiecteDeInventar />)
})


app.get('/creeaza-declaratii', (c) => {
  return c.html(<CreeazaDeclaratii />)
})

app.get('/setari-aplicatie', (c) => {
  return c.html(<SetariAplicatie />)
})

app.get('/seteaza-prag-mijloc-fix', (c) => {
  return c.html(<SetariPragMijlocFix />)
})


console.info("\nHono server started...\n")

Bun.serve({
  port: 5173,
  hostname: "127.0.0.1",
  development: false,
  fetch: app.fetch
})
