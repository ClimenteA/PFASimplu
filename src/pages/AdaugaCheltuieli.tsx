import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"
import { PageHeader } from '../components/PageHeader'



export const AdaugaCheltuieli: FC = () => {
    return (
        <Layout>

            <PageHeader
                title='Adauga Cheltuieli'
                description='Adauga documentele care justifica cheltuielile deductibile facute (Facturi, Bonuri fiscale, etc).'
            />

        </Layout>
    )
}