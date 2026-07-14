"""Demo data seeding. Fictional tenants, users and tickets only (PT-BR content)."""

from datetime import timedelta
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.application.services.sla import FIRST_RESPONSE_WINDOWS
from app.application.services.ticket_service import TicketService
from app.core.security import hash_password
from app.domain.enums import SenderType, TicketPriority, TicketStatus
from app.infra.database.repositories.base import utcnow

COLLECTIONS = [
    "tickets",
    "ticket_messages",
    "ticket_events",
    "channel_payloads",
    "notifications",
    "contacts",
    "tenants",
    "users",
    "counters",
]

DEMO_PASSWORD = "demo123"


class SeedService:
    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.tickets = TicketService(db)

    async def reset(self) -> dict[str, Any]:
        for name in COLLECTIONS:
            await self.db[name].delete_many({})
        return {"status": "reset", "collections": COLLECTIONS}

    async def seed(self) -> dict[str, Any]:
        await self.reset()
        now = utcnow()
        password = hash_password(DEMO_PASSWORD)

        tenants = {}
        for name, slug, document in [
            ("Demo Telecom", "demo-telecom", "00.000.000/0001-00"),
            ("Fiber Works", "fiber-works", "11.111.111/0001-11"),
            ("NetBuild Solutions", "netbuild-solutions", "22.222.222/0001-22"),
        ]:
            result = await self.db.tenants.insert_one(
                {
                    "name": name,
                    "slug": slug,
                    "document": document,
                    "status": "active",
                    "created_at": now,
                    "updated_at": now,
                }
            )
            tenants[slug] = str(result.inserted_id)

        users = {}
        for name, email, role, tenant_id in [
            ("Admin Demo", "admin@demo.com", "admin", None),
            ("Agente Demo", "agent@demo.com", "agent", None),
            ("Jumael", "jumael@demo.com", "agent", None),
            ("Cliente Demo", "tenant@demo.com", "tenant_user", tenants["demo-telecom"]),
            ("Viewer Demo", "viewer@demo.com", "viewer", None),
        ]:
            result = await self.db.users.insert_one(
                {
                    "name": name,
                    "email": email,
                    "password_hash": password,
                    "role": role,
                    "tenant_id": tenant_id,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            users[email] = {"id": str(result.inserted_id), "name": name, "email": email}

        for tenant_slug, name, email, phone in [
            ("demo-telecom", "Carlos Silva", "carlos@demo.com", "+5571999999999"),
            ("demo-telecom", "Ana Lima", "ana@demo.com", "+5571988888888"),
            ("fiber-works", "Maria Souza", "maria@fiberworks.com", "+5511977777777"),
            ("netbuild-solutions", "João Pereira", "joao@netbuild.com", "+5521966666666"),
        ]:
            await self.db.contacts.insert_one(
                {
                    "tenant_id": tenants[tenant_slug],
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "role": "requester",
                    "channels": ["whatsapp", "manual"],
                    "created_at": now,
                    "updated_at": now,
                }
            )

        agent = users["agent@demo.com"]
        jumael = users["jumael@demo.com"]
        admin_email = "admin@demo.com"

        async def create(tenant_slug, requester, title, description, type_, priority, channel,
                         age_hours: float = 0.5):
            ticket = await self.tickets.create_ticket(
                {
                    "tenant_id": tenants[tenant_slug],
                    "requester": requester,
                    "title": title,
                    "description": description,
                    "type": type_,
                    "priority": priority,
                    "source_channel": channel,
                    "tags": [],
                    "metadata": {"origin": "seed"},
                },
                created_by="seed@demo.com",
            )
            if age_hours:
                created_at = now - timedelta(hours=age_hours)
                due = created_at + FIRST_RESPONSE_WINDOWS[TicketPriority(priority)]
                await self.tickets.tickets.col.update_one(
                    {"code": ticket["code"]},
                    {
                        "$set": {
                            "created_at": created_at,
                            "sla.first_response_due_at": due,
                        }
                    },
                )
            return await self.tickets.require_by_code(ticket["code"])

        carlos = {"name": "Carlos Silva", "email": "carlos@demo.com",
                  "phone": "+5571999999999", "channel": "whatsapp"}
        ana = {"name": "Ana Lima", "email": "ana@demo.com",
               "phone": "+5571988888888", "channel": "manual"}
        maria = {"name": "Maria Souza", "email": "maria@fiberworks.com",
                 "phone": "+5511977777777", "channel": "whatsapp"}
        joao = {"name": "João Pereira", "email": "joao@netbuild.com",
                "phone": "+5521966666666", "channel": "telegram"}

        # HD-0001 — in analysis, assigned, first response met, attachment
        t1 = await create("demo-telecom", carlos, "Erro ao finalizar reserva de material",
                          "Usuário informou erro ao finalizar reserva de material na obra OBR-102.",
                          "bug", "high", "whatsapp", age_hours=2)
        await self.tickets.add_message(
            t1["id"], SenderType.TENANT, "Carlos Silva",
            "Não consigo finalizar a reserva de material na obra OBR-102.",
            sender_contact="+5571999999999", channel="whatsapp",
            attachments=[{"type": "image", "url": "https://placehold.co/600x400.png",
                          "filename": "erro-reserva.png"}],
        )
        await self.tickets.add_message(
            t1["id"], SenderType.AGENT, agent["name"],
            "Olá Carlos! Estamos analisando o erro. Pode informar o código da reserva?",
            created_by=agent["email"],
        )
        await self.tickets.change_status(t1["id"], TicketStatus.IN_ANALYSIS, admin_email)
        await self.tickets.assign(t1["id"], agent["id"], agent["name"], admin_email)

        # HD-0002 — overdue medium (30h old, 24h window)
        await create("demo-telecom", ana, "Dúvida sobre relatório de fotos",
                     "Cliente com dúvida sobre como exportar o relatório de fotos da obra.",
                     "question", "medium", "telegram", age_hours=30)

        # HD-0003 — in progress, assigned to Jumael
        t3 = await create("fiber-works", maria, "Solicitação de nova permissão de usuário",
                          "Solicita permissão de aprovador para o usuário da obra OBR-310.",
                          "support", "medium", "manual", age_hours=6)
        await self.tickets.add_message(t3["id"], SenderType.AGENT, jumael["name"],
                                       "Estamos providenciando a permissão solicitada.",
                                       created_by=jumael["email"])
        await self.tickets.change_status(t3["id"], TicketStatus.IN_PROGRESS, admin_email)
        await self.tickets.assign(t3["id"], jumael["id"], jumael["name"], admin_email)

        # HD-0004 — open improvement
        await create("netbuild-solutions", joao, "Melhoria no filtro de obras",
                     "Sugestão: permitir filtrar obras por região e status ao mesmo tempo.",
                     "improvement", "low", "webhook", age_hours=10)

        # HD-0005 — critical overdue (3h old, 2h window)
        await create("demo-telecom", carlos, "Erro ao anexar evidência",
                     "Sistema retorna erro 500 ao anexar evidência em chamados de vistoria.",
                     "bug", "critical", "whatsapp", age_hours=3)

        # HD-0006 — critical incident in progress, responded
        t6 = await create("fiber-works", maria, "Sistema fora do ar na obra OBR-204",
                          "Equipe da obra OBR-204 sem acesso ao sistema desde as 8h.",
                          "incident", "critical", "manual", age_hours=1)
        await self.tickets.add_message(t6["id"], SenderType.AGENT, agent["name"],
                                       "Equipe de infraestrutura acionada, atuando na correção.",
                                       created_by=agent["email"])
        await self.tickets.change_status(t6["id"], TicketStatus.IN_PROGRESS, admin_email)
        await self.tickets.assign(t6["id"], agent["id"], agent["name"], admin_email)

        # HD-0007 — waiting internal
        t7 = await create("netbuild-solutions", joao, "Integração com ERP interno",
                          "Solicita integração do helpdesk com o ERP interno da empresa.",
                          "feature_request", "medium", "demo", age_hours=20)
        await self.tickets.add_message(t7["id"], SenderType.AGENT, agent["name"],
                                       "Encaminhado para o time de produto avaliar viabilidade.",
                                       created_by=agent["email"])
        await self.tickets.change_status(t7["id"], TicketStatus.WAITING_INTERNAL, admin_email)

        # HD-0008 — resolved
        t8 = await create("demo-telecom", ana, "Atualização de cadastro da empresa",
                          "Solicita atualização do endereço fiscal no cadastro.",
                          "support", "low", "manual", age_hours=40)
        await self.tickets.resolve(t8["id"], "Cadastro atualizado conforme solicitado.",
                                   agent["email"], agent["name"])

        # HD-0009 — waiting customer
        t9 = await create("fiber-works", maria, "Dúvida sobre fatura de julho",
                          "Cliente questiona valores da fatura de julho.",
                          "question", "medium", "whatsapp", age_hours=8)
        await self.tickets.add_message(t9["id"], SenderType.AGENT, agent["name"],
                                       "Enviamos o detalhamento da fatura. Pode confirmar?",
                                       created_by=agent["email"])
        await self.tickets.change_status(t9["id"], TicketStatus.WAITING_CUSTOMER, admin_email)

        # HD-0010 — high overdue (5h old, 4h window)
        await create("netbuild-solutions", joao, "Erro de sincronização no app de campo",
                     "App de campo não sincroniza apontamentos desde ontem.",
                     "bug", "high", "telegram", age_hours=5)

        # HD-0011 — closed
        t11 = await create("demo-telecom", carlos, "Treinamento para nova equipe",
                           "Solicita treinamento de onboarding para 5 novos usuários.",
                           "support", "low", "demo", age_hours=72)
        await self.tickets.resolve(t11["id"], "Treinamento realizado em 10/07.",
                                   agent["email"], agent["name"])
        await self.tickets.change_status(t11["id"], TicketStatus.CLOSED, admin_email)

        # HD-0012 — cancelled
        t12 = await create("fiber-works", maria, "Chamado duplicado sobre fatura",
                           "Aberto em duplicidade com HD-0009.",
                           "support", "medium", "webhook", age_hours=7)
        await self.tickets.change_status(t12["id"], TicketStatus.CANCELLED, admin_email)

        # HD-0013 — near due (3h old, 4h window -> 25% remaining)
        await create("netbuild-solutions", joao, "Lentidão no módulo de medições",
                     "Módulo de medições muito lento em horários de pico.",
                     "incident", "high", "manual", age_hours=3.1)

        # HD-0014 — recent open question
        await create("demo-telecom", ana, "Como exportar relatório em PDF?",
                     "Dúvida simples sobre exportação de relatórios em PDF.",
                     "question", "low", "telegram", age_hours=0.2)

        # HD-0015 — reopened after tenant reply
        t15 = await create("fiber-works", maria, "Erro intermitente ao aprovar medição",
                           "Erro intermitente ao aprovar medições no fluxo financeiro.",
                           "bug", "medium", "whatsapp", age_hours=26)
        await self.tickets.resolve(t15["id"], "Correção aplicada na versão 2.4.1.",
                                   agent["email"], agent["name"])
        await self.tickets.add_message(
            t15["id"], SenderType.TENANT, "Maria Souza",
            "O erro voltou a acontecer hoje de manhã.",
            sender_contact="+5511977777777", channel="whatsapp",
        )

        return {
            "status": "seeded",
            "tenants": len(tenants),
            "users": len(users),
            "tickets": await self.db.tickets.count_documents({}),
            "demo_logins": [
                {"email": "admin@demo.com", "password": DEMO_PASSWORD, "role": "admin"},
                {"email": "agent@demo.com", "password": DEMO_PASSWORD, "role": "agent"},
                {"email": "tenant@demo.com", "password": DEMO_PASSWORD, "role": "tenant_user"},
                {"email": "viewer@demo.com", "password": DEMO_PASSWORD, "role": "viewer"},
            ],
        }
