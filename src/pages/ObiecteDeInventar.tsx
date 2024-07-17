import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"
import { PageHeader } from '../components/PageHeader'



export const ObiecteDeInventar: FC = () => {
    return (
        <Layout>

            <PageHeader
                title='Obiecte De Inventar'
                description='Aici sunt toate obiectele de inventar si mijloacele fixe achizitionate pana acum 
                in scopul desfasurarii activitatii.'
            />

        </Layout>
    )
}