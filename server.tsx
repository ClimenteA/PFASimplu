import { Hono } from 'hono'
import type { FC } from 'hono/jsx'
import { serveStatic } from 'hono/bun'
import { useRequestContext } from 'hono/jsx-renderer'


const app = new Hono()

app.use('/static/*', serveStatic({ root: `./` }))


const Aside: FC<{activeLink: string}> = (props: {activeLink: string}) => {
  return (
    <aside class="menu has-background-grey-darker" style="min-width: 250px;">
      <p class="menu-label">Meniu</p>
      <ul class="menu-list">
        <li>
          <a class={props.activeLink == 'registre-contabile' ? "is-active has-text-white is-flex" : "has-background-grey-darker has-text-white is-flex"}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" style="margin-right: 5px;" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
            </svg>
            <span>Registre contabile</span>
          </a></li>
        <li>
          <a class={props.activeLink == 'creeaza-factura' ? "is-active has-text-white is-flex" : "has-background-grey-darker has-text-white is-flex"}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" style="margin-right: 5px;" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 11.625h4.5m-4.5 2.25h4.5m2.121 1.527c-1.171 1.464-3.07 1.464-4.242 0-1.172-1.465-1.172-3.84 0-5.304 1.171-1.464 3.07-1.464 4.242 0M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
            <span>Creeaza factura</span>
          </a></li>
        <li>
          <a class={props.activeLink == 'adauga-incasari' ? "is-active has-text-white is-flex" : "has-background-grey-darker has-text-white is-flex"}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" style="margin-right: 5px;" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.25 7.756a4.5 4.5 0 1 0 0 8.488M7.5 10.5h5.25m-5.25 3h5.25M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
            <span>Adauga incasari</span>
          </a></li>
        <li>
          <a class={props.activeLink == 'adauga-cheltuieli' ? "is-active has-text-white is-flex" : "has-background-grey-darker has-text-white is-flex"}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" style="margin-right: 5px;" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="m9 14.25 6-6m4.5-3.493V21.75l-3.75-1.5-3.75 1.5-3.75-1.5-3.75 1.5V4.757c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0c1.1.128 1.907 1.077 1.907 2.185ZM9.75 9h.008v.008H9.75V9Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm4.125 4.5h.008v.008h-.008V13.5Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
            </svg>
            <span>Adauga cheltuieli</span>
          </a></li>
        <li>
          <a class={props.activeLink == 'adauga-declaratii' ? "is-active has-text-white is-flex" : "has-background-grey-darker has-text-white is-flex"}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" style="margin-right: 5px;" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 8.25V6a2.25 2.25 0 0 0-2.25-2.25H6A2.25 2.25 0 0 0 3.75 6v8.25A2.25 2.25 0 0 0 6 16.5h2.25m8.25-8.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-7.5A2.25 2.25 0 0 1 8.25 18v-1.5m8.25-8.25h-6a2.25 2.25 0 0 0-2.25 2.25v6" />
            </svg>
            <span>Adauga declaratii</span>
          </a></li>
        <li>
          <a class={props.activeLink == 'obiecte-de-inventar' ? "is-active has-text-white is-flex" : "has-background-grey-darker has-text-white is-flex"}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" style="margin-right: 5px;" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 0 1-.657.643 48.39 48.39 0 0 1-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 0 1-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 0 0-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 0 1-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 0 0 .657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 0 1-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 0 0 5.427-.63 48.05 48.05 0 0 0 .582-4.717.532.532 0 0 0-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.96.401v0a.656.656 0 0 0 .658-.663 48.422 48.422 0 0 0-.37-5.36c-1.886.342-3.81.574-5.766.689a.578.578 0 0 1-.61-.58v0Z" />
            </svg>
            <span>Obiecte de inventar</span>
          </a></li>
        <li>
          <a class={props.activeLink == 'creeaza-declaratii' ? "is-active has-text-white is-flex" : "has-background-grey-darker has-text-white is-flex"}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" style="margin-right: 5px;" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
            </svg>
            <span>Creeaza declaratii</span>
          </a></li>
        <li>
          <a class={props.activeLink == 'setari-aplicatie' ? "is-active has-text-white is-flex" : "has-background-grey-darker has-text-white is-flex"}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" style="margin-right: 5px;" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75a4.5 4.5 0 0 1-4.884 4.484c-1.076-.091-2.264.071-2.95.904l-7.152 8.684a2.548 2.548 0 1 1-3.586-3.586l8.684-7.152c.833-.686.995-1.874.904-2.95a4.5 4.5 0 0 1 6.336-4.486l-3.276 3.276a3.004 3.004 0 0 0 2.25 2.25l3.276-3.276c.256.565.398 1.192.398 1.852Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.867 19.125h.008v.008h-.008v-.008Z" />
            </svg>
            <span>Setari aplicatie</span>
          </a></li>
      </ul>
    </aside>
  )
}



const Layout: FC = (props) => {
  return (
    <html>
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="stylesheet" href="/static/bulma.min.css" />
        <title>PFASimplu</title>
      </head>
      <body class="is-flex">

        <Aside activeLink={props.activeLink}/>

        <main class="px-4">
          {props.children}
        </main>

      </body>
    </html>
  )
}


const RegistreContabile: FC<{ activeLink: string }> = (props: {activeLink: string}) => {
  return (
    <Layout props={props.activeLink}>

      <h1>Registre contabile</h1>

    </Layout>
  )
}


app.get('/', (c) => {
  console.log(c.req.url)
  return c.html(<RegistreContabile activeLink='registre-contabile' />)
})




console.info("\nHono server started...\n")

Bun.serve({
  port: 5173,
  hostname: "127.0.0.1",
  development: false,
  fetch: app.fetch
})