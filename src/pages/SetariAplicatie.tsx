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

            <div className="mt-12">

                <a href='/seteaza-prag-mijloc-fix' className="btn">
                    Seteaza prag mijloc fix
                </a>

            </div>


        </Layout>
    )
}