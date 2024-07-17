import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"
import { PageHeader } from '../components/PageHeader'



export const AdaugaDeclaratii: FC = () => {
    return (
        <Layout>

            <PageHeader
                title='Adauga Declaratii'
                description='Adauga declaratiile depuse la ANAF si dovezile de plata impozite sau alte documente.'
            />

        </Layout>
    )
}