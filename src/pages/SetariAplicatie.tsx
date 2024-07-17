import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"
import { PageHeader } from '../components/PageHeader'


export const SetariAplicatie: FC = () => {
    return (
        <Layout>

            <PageHeader
                title='Setari Aplicatie'
                description='Aici poti seta variabilele care stau la baza calculului 
                impozitelor, taxelor, creearea de declaratii, date PFA, etc. (salariul minim brut, procente taxe etc.)'
            />

            <a href='/seteaza-prag-mijloc-fix' className="inline-block badge badge-lg badge-neutral hover:underline">
                Seteaza prag mijloc fix
            </a>

        </Layout>
    )
}