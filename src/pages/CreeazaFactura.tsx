import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"
import { PageHeader } from '../components/PageHeader'



export const CreeazaFactura: FC = () => {
    return (
        <Layout>

            <PageHeader
                title='Creeaza Factura'
                description='Creeaza o factura PDF + XML necesar pentru E-Factura. Aplicatia va incerca sa o trimita catre ANAF.'
            />

        </Layout>
    )
}