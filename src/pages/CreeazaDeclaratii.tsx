import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"
import { PageHeader } from '../components/PageHeader'



export const CreeazaDeclaratii: FC = () => {
    return (
        <Layout>

            <PageHeader
                title='Creeaza Declaratii'
                description='Declaratii ANAF precum: Declaratia Unica 212, Declaratie TVA in Romania 394, 
                Declaratie Decont TVA 300, Declaratie Tranzactii Intracomunitare 390, Declaratie salariati 112'
            />

        </Layout>
    )
}