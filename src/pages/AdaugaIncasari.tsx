import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"
import { PageHeader } from '../components/PageHeader'



export const AdaugaIncasari: FC = () => {
    return (
        <Layout>

            <PageHeader
                title='Adauga Incasari'
                description='Adauga documentele justificative pentru incasarile primite (Facturi). Zip-ul care contine E-Factura in format XML/PDF.'
            />

        </Layout>
    )
}