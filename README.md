# 🕵️‍♂️ Integração Wazuh & Sophos Central API

![Banner da Integração Wazuh e Sophos](image)

## 📄 Sumário

Este projeto oferece uma solução robusta e completa para integrar os logs de **Alertas** e **Eventos** da API SIEM da Sophos Central diretamente com o seu ambiente Wazuh.

Através de um script Python inteligente e um conjunto de regras personalizadas, esta integração capacita seu SIEM a monitorar, alertar e responder em tempo real a uma vasta gama de eventos de segurança gerados por toda a suite de produtos Sophos, desde o Intercept X até o Firewall.

---

## ✨ Funcionalidades Principais

* **Coleta Abrangente**: Busca dados dos endpoints `/alerts` e `/events` da API da Sophos.

* **Mecanismo de Cursor Persistente**: Utiliza um sistema de cursor que salva o progresso a cada coleta, garantindo que nenhum log seja perdido ou duplicado.

* **Configuração Segura e Centralizada**: Gerencia todas as credenciais e configurações da API de forma segura através de um arquivo `.env`, mantendo dados sensíveis fora do código principal.

* **+25 Regras Personalizadas para Wazuh**: Inclui um conjunto de regras prontas para uso que cobrem diversos produtos e eventos da Sophos:
    * 🔥 **Firewall**: Status de Gateway e túneis VPN, detecções de ATP.
    * 🛡️ **IPS**: Detecção e bloqueio de ataques.
    * 📁 **FIM (File Integrity Monitoring)**: Detecção de alterações em arquivos críticos.
    * 📧 **Email Security**: Detecção de Phishing e Malware.
    * 🌐 **Web Control & DNS Protection**: Bloqueio de categorias e domínios maliciosos.
    * 💻 **Intercept X**: Detecção, limpeza e quarentena de ameaças.
    * E muito mais!

* **Mapeamento com MITRE ATT&CK®**: Enriquecimento dos alertas com táticas e técnicas do framework MITRE ATT&CK®, facilitando a análise e resposta a incidentes.

---

## 📋 Pré-requisitos

| Requisito                               | Detalhes                                                                                                               |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Acesso ao Manager Wazuh** | Privilégios de administrador são necessários para instalar scripts e configurar o `ossec.conf`.                            |
| **Python 3** | Essencial para a execução do script de coleta. A biblioteca `python-dotenv` também é necessária.                        |
| **Credenciais da API da Sophos Central** | Você precisará do `Client ID`, `Client Secret`, `Tenant ID` e dos Hosts de API corretos para a sua região da Sophos. |

---

## 🚀 Guia de Instalação e Configuração

Siga estes passos detalhadamente no seu **Wazuh Manager** para uma implementação bem-sucedida.

### Etapa 1: Configuração da API na Sophos Central

1.  Acesse seu painel da **Sophos Central**.
2.  Navegue até **Global Settings > API Credentials**.
3.  Crie uma nova credencial com o papel de **"Service Principal SIEM"**. Este papel garante que a API tenha apenas as permissões de leitura necessárias.
4.  Guarde com segurança seu **Client ID**, **Client Secret**, **Tenant ID** e os **Hosts da API**.

### Etapa 2: Preparação do Ambiente no Wazuh Manager

1.  **Copie o Script de Coleta**:
    Mova o script `get_sophos_data.py` para o diretório de `wodles` do Wazuh.
    ```bash
    cp get_sophos_data.py /var/ossec/wodles/
    ```

2.  **Instale a Dependência Python**:
    ```bash
    pip3 install python-dotenv
    ```

3.  **Atribua Permissão de Execução**:
    ```bash
    chmod +x /var/ossec/wodles/get_sophos_data.py
    ```

### Etapa 3: Configuração das Credenciais (`.env`)

1.  **Crie o Arquivo de Ambiente**:
    No diretório `/var/ossec/wodles/`, crie o arquivo `.env`.
    ```bash
    touch /var/ossec/wodles/.env
    ```

2.  **Adicione suas Credenciais**:
    Edite o arquivo `.env` e insira as credenciais que você obteve da Sophos.
    ```dotenv
    # /var/ossec/wodles/.env
    SOPHOS_CLIENT_ID="SEU_CLIENT_ID_AQUI"
    SOPHOS_CLIENT_SECRET="SEU_CLIENT_SECRET_AQUI"
    SOPHOS_TENANT_ID="SEU_TENANT_ID_AQUI"
    SOPHOS_API_AUTH_HOST="id.sophos.com"
    SOPHOS_API_DATA_HOST="api.central.sophos.com"
    ```
    > **🔒 Segurança**: As permissões deste arquivo devem ser restritas. Use `chown ossec:ossec` e `chmod 600` para garantir que apenas o usuário do Wazuh possa acessá-lo.

### Etapa 4: Configuração do Wazuh (`ossec.conf`)

Adicione os seguintes blocos ao seu arquivo `/var/ossec/etc/ossec.conf`.

1.  **Wodle Command (Coleta de Dados)**:
    Este bloco executa o script para buscar `alerts` e `events` da Sophos.
    ```xml
    <!-- Adicionar dentro da tag <ossec_config> -->
    <wodle name="command">
      <disabled>no</disabled>
      <tag>sophos_alerts</tag>
      <command>/usr/bin/python3 /var/ossec/wodles/get_sophos_data.py alerts</command>
      <interval>5m</interval>
      <ignore_output>no</ignore_output>
      <run_on_start>yes</run_on_start>
      <timeout>20</timeout>
    </wodle>

    <wodle name="command">
      <disabled>no</disabled>
      <tag>sophos_events</tag>
      <command>/usr/bin/python3 /var/ossec/wodles/get_sophos_data.py events</command>
      <interval>5m</interval>
      <ignore_output>no</ignore_output>
      <run_on_start>yes</run_on_start>
      <timeout>20</timeout>
    </wodle>
    ```

2.  **Localfile (Leitura dos Logs)**:
    Este bloco instrui o Wazuh a ler os logs JSON gerados pelo script.
    ```xml
    <!-- Adicionar dentro da tag <ossec_config> -->
    <localfile>
      <log_format>json</log_format>
      <location>/var/log/sophos-api.log</location>
    </localfile>
    ```

### Etapa 5: Instalação das Regras Personalizadas

1.  Copie todo o conteúdo do arquivo `local_rules.xml`.
2.  Adicione-o ao seu arquivo de regras em `/var/ossec/etc/rules/local_rules.xml`. Cole o conteúdo dentro da tag raiz `<group>`.

### Etapa 6: Finalização

1.  **Ajuste de Permissões**:
    Garanta que o usuário `ossec` tenha permissão para escrever no log e nos arquivos de cursor.
    ```bash
    chown ossec:ossec /var/ossec/wodles/get_sophos_data.py
    chown ossec:ossec /var/ossec/wodles/.env
    touch /var/log/sophos-api.log
    chown ossec:ossec /var/log/sophos-api.log
    touch /var/ossec/wodles/sophos_cursor_events.txt
    touch /var/ossec/wodles/sophos_cursor_alerts.txt
    chown ossec:ossec /var/ossec/wodles/sophos_cursor_*
    ```

2.  **Reinicie o Wazuh Manager**:
    Aplique todas as mudanças.
    ```bash
    systemctl restart wazuh-manager
    ```

---

## ⚙️ Arquitetura da Solução

O fluxo de dados da integração opera da seguinte forma:

1.  **Execução Agendada**: O `Wodle` do Wazuh executa o script `get_sophos_data.py` a cada 5 minutos.
2.  **Autenticação**: O script obtém um token de acesso temporário da API da Sophos usando as credenciais do `.env`.
3.  **Coleta Inteligente**: Ele lê o último cursor salvo para saber de onde continuar a coleta de dados.
4.  **Ingestão de Logs**: Os eventos e alertas recebidos são escritos como linhas JSON no arquivo `/var/log/sophos-api.log`.
5.  **Análise e Alerta**: O `Logcollector` do Wazuh monitora este arquivo e envia os logs para o motor de análise, que os compara com as regras personalizadas para gerar alertas no painel.

---

## 🔧 Troubleshooting

* **Erro de Variáveis de Ambiente**: Verifique se o arquivo `/var/ossec/wodles/.env` existe e se as credenciais estão corretas.

* **Erro de Permissão de Escrita**: Execute os comandos de `chown` da Etapa 6 para corrigir as permissões do log e dos arquivos de cursor.

* **Nenhum Alerta no Painel**:
    1.  Verifique `/var/ossec/logs/ossec.log` para erros relacionados ao `wodle` ou `sophos-api`.
    2.  Confirme se `/var/log/sophos-api.log` está recebendo dados. Se estiver vazio, o problema está na comunicação com a API da Sophos.
    3.  Use a ferramenta `wazuh-logtest` para validar suas regras com uma linha de log do arquivo `sophos-api.log`.
