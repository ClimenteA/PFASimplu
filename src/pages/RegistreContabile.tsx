import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"
import { PageHeader } from '../components/PageHeader'


export const RegistreContabile: FC = () => {
    return (
        <Layout>

            <PageHeader
                title='Registre contabile'
                description='Aici sunt registrele contabile generate automat din 
                incasari, cheltuieli si alte actiuni facute in aplicatie.'
            />

        </Layout>
    )
}