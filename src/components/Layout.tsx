import type { FC } from 'hono/jsx'
import { NavBar } from './NavBar'


export const Layout: FC = (props) => {
    return (
        <html>
            <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link rel="stylesheet" href="/static/output.css" />
                <title>PFASimplu</title>
            </head>
            <body class="container mx-auto">

                <NavBar />

                <main class="px-4">
                    {props.children}
                </main>

            </body>
        </html>
    )
}
