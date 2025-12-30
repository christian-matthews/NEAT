"""
Servicio de integración con Airtable.
Proporciona una capa de abstracción para todas las operaciones CRUD con Airtable.
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
from pydantic import BaseModel, Field


class AirtableConfig(BaseModel):
    """Configuración para conexión a Airtable."""
    api_key: str
    base_id: str
    table_cargos: str = "Cargos"
    table_procesos: str = "Procesos"  # Tabla nueva
    table_candidatos: str = "Postulaciones"  # Tabla nueva (antes "Candidatos")
    table_evaluaciones: str = "Evaluaciones_AI"
    table_comentarios: str = "Comentarios"
    table_entrevistas: str = "Entrevistas"
    table_config: str = "Config_Evaluacion"
    table_usuarios: str = "Usuarios"
    table_historial: str = "Historial_Estados"
    
    @classmethod
    def from_env(cls) -> "AirtableConfig":
        """Carga configuración desde variables de entorno."""
        api_key = os.getenv("AIRTABLE_API_KEY")
        base_id = os.getenv("AIRTABLE_BASE_ID")
        
        if not api_key:
            raise ValueError("AIRTABLE_API_KEY no está configurado")
        if not base_id:
            raise ValueError("AIRTABLE_BASE_ID no está configurado")
        
        return cls(
            api_key=api_key,
            base_id=base_id,
            table_cargos=os.getenv("AIRTABLE_TABLE_CARGOS", "Cargos"),
            table_procesos=os.getenv("AIRTABLE_TABLE_PROCESOS", "Procesos"),
            table_candidatos=os.getenv("AIRTABLE_TABLE_CANDIDATOS", "Postulaciones"),
            table_evaluaciones=os.getenv("AIRTABLE_TABLE_EVALUACIONES", "Evaluaciones_AI"),
            table_comentarios=os.getenv("AIRTABLE_TABLE_COMENTARIOS", "Comentarios"),
            table_entrevistas=os.getenv("AIRTABLE_TABLE_ENTREVISTAS", "Entrevistas"),
            table_config=os.getenv("AIRTABLE_TABLE_CONFIG", "Config_Evaluacion"),
            table_usuarios=os.getenv("AIRTABLE_TABLE_USUARIOS", "Usuarios"),
            table_historial=os.getenv("AIRTABLE_TABLE_HISTORIAL", "Historial_Estados"),
        )


class AirtableService:
    """
    Servicio de conexión a Airtable.
    
    Uso:
        service = AirtableService.from_env()
        
        # Obtener candidatos
        candidatos = await service.get_candidatos()
        
        # Crear candidato
        nuevo = await service.create_candidato({
            "nombre_completo": "Juan Pérez",
            "email": "juan@email.com"
        })
    """
    
    BASE_URL = "https://api.airtable.com/v0"
    
    def __init__(self, config: AirtableConfig):
        self.config = config
        self._headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def from_env(cls) -> "AirtableService":
        """Crea una instancia desde variables de entorno."""
        return cls(AirtableConfig.from_env())
    
    def _get_table_url(self, table_name: str) -> str:
        """Construye la URL para una tabla."""
        return f"{self.BASE_URL}/{self.config.base_id}/{table_name}"
    
    # =========================================================================
    # Generic CRUD Operations
    # =========================================================================
    
    async def _get_records(
        self,
        table_name: str,
        filter_formula: Optional[str] = None,
        sort: Optional[List[Dict[str, str]]] = None,
        max_records: Optional[int] = None,
        view: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene registros de una tabla.
        
        Args:
            table_name: Nombre de la tabla
            filter_formula: Fórmula de filtro de Airtable
            sort: Lista de ordenamientos [{field, direction}]
            max_records: Límite de registros
            view: Nombre de la vista a usar
            
        Returns:
            Lista de registros
        """
        url = self._get_table_url(table_name)
        params = {}
        
        if filter_formula:
            params["filterByFormula"] = filter_formula
        if sort:
            for i, s in enumerate(sort):
                params[f"sort[{i}][field]"] = s.get("field")
                params[f"sort[{i}][direction]"] = s.get("direction", "asc")
        if max_records:
            params["maxRecords"] = max_records
        if view:
            params["view"] = view
        
        all_records = []
        offset = None
        
        async with httpx.AsyncClient() as client:
            while True:
                if offset:
                    params["offset"] = offset
                
                response = await client.get(url, headers=self._headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                records = data.get("records", [])
                all_records.extend(records)
                
                offset = data.get("offset")
                if not offset:
                    break
        
        return all_records
    
    async def _get_record(self, table_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un registro por ID."""
        url = f"{self._get_table_url(table_name)}/{record_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    async def _create_record(self, table_name: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo registro."""
        url = self._get_table_url(table_name)
        payload = {"fields": fields}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self._headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def _update_record(
        self,
        table_name: str,
        record_id: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Actualiza un registro existente."""
        url = f"{self._get_table_url(table_name)}/{record_id}"
        payload = {"fields": fields}
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=self._headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def _delete_record(self, table_name: str, record_id: str) -> bool:
        """Elimina un registro."""
        url = f"{self._get_table_url(table_name)}/{record_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self._headers)
            return response.status_code == 200
    
    async def _find_record_by_field(
        self,
        table_name: str,
        field_name: str,
        value: str
    ) -> Optional[Dict[str, Any]]:
        """Busca un registro por un campo específico."""
        filter_formula = f"{{{field_name}}} = '{value}'"
        records = await self._get_records(table_name, filter_formula=filter_formula, max_records=1)
        return records[0] if records else None
    
    # =========================================================================
    # Candidatos
    # =========================================================================
    
    async def get_candidatos(
        self,
        proceso_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los candidatos, opcionalmente filtrados por proceso."""
        # Obtener todos los registros
        records = await self._get_records(
            self.config.table_candidatos,
            max_records=limit if not proceso_id else None
        )
        
        candidatos = [self._format_candidato(r) for r in records]
        
        # Filtrar por proceso si se especifica
        if proceso_id:
            candidatos = [
                c for c in candidatos 
                if proceso_id in (c.get("proceso") or [])
            ]
            
            # Aplicar límite después del filtro
            if limit:
                candidatos = candidatos[:limit]
        
        return candidatos
    
    async def get_candidato(self, tracking_code: str) -> Optional[Dict[str, Any]]:
        """Obtiene un candidato por su código de tracking."""
        record = await self._find_record_by_field(
            self.config.table_candidatos,
            "codigo_tracking",
            tracking_code
        )
        return self._format_candidato(record) if record else None
    
    async def get_candidato_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un candidato por su ID de Airtable."""
        record = await self._get_record(self.config.table_candidatos, record_id)
        return self._format_candidato(record) if record else None
    
    async def create_candidato(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva postulación/candidato."""
        fields = {
            "codigo_tracking": data.get("codigo_tracking"),
            "nombre_completo": data.get("nombre_completo"),
            "email": data.get("email"),
            "telefono": data.get("telefono"),
            "estado_candidato": data.get("estado_candidato", "nuevo"),
        }
        
        # URL del CV (para compatibilidad)
        if data.get("cv_url"):
            fields["cv_url"] = data["cv_url"]
        
        # Attachment del CV (para Airtable)
        # Formato esperado: [{"url": "https://..."}]
        if data.get("cv_archivo"):
            fields["cv_archivo"] = data["cv_archivo"]
        
        # Fecha de postulación
        if data.get("fecha_postulacion"):
            fields["fecha_postulacion"] = data["fecha_postulacion"]
        
        # Manejar relaciones (enlaces a otras tablas)
        # Soporta tanto proceso_id como proceso (lista directa)
        if data.get("proceso_id"):
            fields["proceso"] = [data["proceso_id"]]
        elif data.get("proceso"):
            fields["proceso"] = data["proceso"] if isinstance(data["proceso"], list) else [data["proceso"]]
        
        if data.get("cargo_id"):
            fields["cargo"] = [data["cargo_id"]]
        elif data.get("cargo"):
            fields["cargo"] = data["cargo"] if isinstance(data["cargo"], list) else [data["cargo"]]
        
        record = await self._create_record(self.config.table_candidatos, fields)
        return self._format_candidato(record)
    
    async def update_candidato(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un candidato existente."""
        # Filtrar campos que pueden no existir en Airtable
        # para evitar errores 422
        safe_fields = {}
        
        # Campos que sabemos que existen
        known_fields = [
            "codigo_tracking", "nombre_completo", "email", "telefono",
            "cv_url", "cv_archivo", "estado_candidato", "notas", "tags",
            # Campos nuevos de OpenAI (agregar en Airtable si no existen)
            "cv_texto", "cv_data_json", "años_experiencia", 
            "titulo_profesional", "resumen_perfil"
        ]
        
        for key, value in data.items():
            if key in known_fields:
                safe_fields[key] = value
        
        if not safe_fields:
            return await self.get_candidato_by_id(record_id) or {}
        
        try:
            record = await self._update_record(self.config.table_candidatos, record_id, safe_fields)
            return self._format_candidato(record)
        except Exception as e:
            # Si falla, intentar sin los campos nuevos
            print(f"[WARN] Error actualizando candidato, reintentando sin campos OpenAI: {e}")
            basic_fields = {k: v for k, v in safe_fields.items() 
                          if k not in ["cv_texto", "cv_data_json", "años_experiencia", 
                                       "titulo_profesional", "resumen_perfil"]}
            if basic_fields:
                record = await self._update_record(self.config.table_candidatos, record_id, basic_fields)
                return self._format_candidato(record)
            return await self.get_candidato_by_id(record_id) or {}
    
    def _format_candidato(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un registro de candidato/postulación de Airtable."""
        if not record:
            return {}
        
        fields = record.get("fields", {})
        
        # Manejar attachments de CV
        cv_url = fields.get("cv_url", "")
        cv_archivo = fields.get("cv_archivo", [])
        if cv_archivo and len(cv_archivo) > 0:
            cv_url = cv_archivo[0].get("url", cv_url)
        
        return {
            "id": record.get("id"),
            "codigo_tracking": fields.get("codigo_tracking", ""),
            "nombre_completo": fields.get("nombre_completo", ""),
            "email": fields.get("email", ""),
            "telefono": fields.get("telefono", ""),
            "cv_url": cv_url,
            "cv_archivo": cv_archivo,
            "estado_candidato": fields.get("estado_candidato", "nuevo"),
            "score_ai": fields.get("score_ai", 0),
            "notas": fields.get("notas", ""),
            "tags": fields.get("tags", []),
            "proceso": fields.get("proceso", []),
            "cargo": fields.get("cargo", []),
            "evaluacion": fields.get("evaluacion", []),
            "created_at": record.get("createdTime")
        }
    
    # =========================================================================
    # Evaluaciones
    # =========================================================================
    
    async def get_evaluacion(self, candidato_id: str, tracking_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene la evaluación de un candidato.
        
        Args:
            candidato_id: Record ID del candidato en Airtable
            tracking_code: Código de tracking (requerido para búsqueda eficiente)
        """
        record = None
        
        # Si tenemos tracking code, buscar por ese campo
        if tracking_code:
            filter_formula = f"{{candidato}} = '{tracking_code}'"
            records = await self._get_records(
                self.config.table_evaluaciones, 
                filter_formula=filter_formula, 
                max_records=1
            )
            record = records[0] if records else None
        else:
            # Fallback: buscar candidato para obtener tracking code
            candidato = await self.get_candidato_by_id(candidato_id)
            if candidato and candidato.get("codigo_tracking"):
                tracking = candidato["codigo_tracking"]
                filter_formula = f"{{candidato}} = '{tracking}'"
                records = await self._get_records(
                    self.config.table_evaluaciones, 
                    filter_formula=filter_formula, 
                    max_records=1
                )
                record = records[0] if records else None
        
        return self._format_evaluacion(record) if record else None
    
    async def create_evaluacion(self, candidato_id: str, evaluation_data: Dict[str, Any], codigo_tracking: Optional[str] = None) -> Dict[str, Any]:
        """Crea o actualiza la evaluación de un candidato.
        
        IMPORTANTE: Si ya existe una evaluación para este candidato, la ACTUALIZA en lugar de crear duplicados.
        """
        
        # =====================================================================
        # VERIFICAR SI YA EXISTE UNA EVALUACIÓN PARA ESTE CANDIDATO
        # =====================================================================
        existing_eval = await self.get_evaluacion(candidato_id, codigo_tracking)
        existing_record_id = existing_eval.get("id") if existing_eval else None
        
        if existing_record_id:
            print(f"[INFO] Evaluación existente encontrada ({existing_record_id}), se actualizará")
        
        # Soportar tanto formato anidado (fits/inference) como formato plano
        fits = evaluation_data.get("fits", {})
        inference = evaluation_data.get("inference", {})
        
        # Si hay datos en formato plano, usar esos
        score_admin = evaluation_data.get("score_admin") or fits.get("admin", {}).get("score", 0)
        score_ops = evaluation_data.get("score_ops") or fits.get("ops", {}).get("score", 0)
        score_biz = evaluation_data.get("score_biz") or fits.get("biz", {}).get("score", 0)
        hands_on = evaluation_data.get("hands_on_index") or inference.get("hands_on_index", 0)
        potential = evaluation_data.get("potential_score") or inference.get("potential_score", 0)
        retention = evaluation_data.get("retention_risk") or inference.get("retention_risk", "Bajo")
        profile = evaluation_data.get("profile_type") or inference.get("profile_type", "")
        industry = evaluation_data.get("industry_tier") or inference.get("industry_tier", "General")
        risk_warning = evaluation_data.get("risk_warning") or inference.get("risk_warning", "")
        
        # Mapear valores a las opciones válidas de Airtable
        # profile_type: ['Corporativo Senior', 'Ejecutor Hands-On', 'Estratégico / Delegador', 'Híbrido']
        # industry_tier: ['Fintech (Ideal)', 'General', 'Tech / Digital', 'Traditional']
        # retention_risk: ['Alto', 'Bajo']
        
        profile_map = {
            "Híbrido (Gestión + Operación)": "Híbrido",
            "Híbrido": "Híbrido",
            "Ejecutor Hands-On": "Ejecutor Hands-On",
            "Ejecutor / Hands-On": "Ejecutor Hands-On",
            "Estratégico / Delegador": "Estratégico / Delegador",
            "Corporativo Senior": "Corporativo Senior",
        }
        profile_normalized = profile_map.get(profile, "Híbrido")
        
        industry_map = {
            "Fintech (Ideal)": "Fintech (Ideal)",
            "Fintech": "Fintech (Ideal)",
            "Tech / Digital": "Tech / Digital",
            "Tech": "Tech / Digital",
            "Digital": "Tech / Digital",
            "Traditional": "Traditional",
            "General": "General",
        }
        industry_normalized = industry_map.get(industry, "General")
        
        retention_normalized = "Alto" if retention in ["Alto", "High"] else "Bajo"
        
        # Timestamp de última actualización (para comparar con comentarios)
        from datetime import datetime
        updated_at = datetime.utcnow().isoformat() + "Z"
        
        fields = {
            "candidato": codigo_tracking or "",
            "score_promedio": evaluation_data.get("score_promedio", 0),
            "score_admin": score_admin,
            "score_ops": score_ops,
            "score_biz": score_biz,
            "hands_on_index": hands_on,
            "potential_score": potential,
            "retention_risk": retention_normalized,
            "profile_type": profile_normalized,
            "industry_tier": industry_normalized,
            "risk_warning": risk_warning,
            "config_version": evaluation_data.get("config_version", "1.0"),
            "updated_at": updated_at,  # Timestamp de última evaluación/re-evaluación
        }
        
        # Solo agregar postulacion si es un ID válido (y solo para nuevos registros)
        if candidato_id and candidato_id.startswith("rec") and not existing_record_id:
            fields["postulacion"] = [candidato_id]
        
        # Agregar keywords encontradas (solo si existe fits anidado)
        if "admin" in fits:
            fields["keywords_found_admin"] = ", ".join(fits["admin"].get("found", []))
            fields["reasoning_admin"] = fits["admin"].get("reasoning", "")
        if "ops" in fits:
            fields["keywords_found_ops"] = ", ".join(fits["ops"].get("found", []))
            fields["reasoning_ops"] = fits["ops"].get("reasoning", "")
        if "biz" in fits:
            fields["keywords_found_biz"] = ", ".join(fits["biz"].get("found", []))
            fields["reasoning_biz"] = fits["biz"].get("reasoning", "")
        
        # =====================================================================
        # ACTUALIZAR O CREAR
        # =====================================================================
        if existing_record_id:
            # ACTUALIZAR el registro existente
            record = await self._update_record(self.config.table_evaluaciones, existing_record_id, fields)
            print(f"[INFO] ✅ Evaluación ACTUALIZADA: {existing_record_id}")
        else:
            # CREAR nuevo registro
            record = await self._create_record(self.config.table_evaluaciones, fields)
            print(f"[INFO] ✅ Evaluación CREADA: {record.get('id')}")
        
        return self._format_evaluacion(record)
    
    async def update_evaluacion(self, record_id: str, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza una evaluación existente."""
        fields = {
            "score_promedio": evaluation_data.get("score_promedio", 0),
            "analysis_json": str(evaluation_data),
        }
        record = await self._update_record(self.config.table_evaluaciones, record_id, fields)
        return self._format_evaluacion(record)
    
    def _format_evaluacion(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un registro de evaluación de Airtable."""
        if not record:
            return {}
        
        fields = record.get("fields", {})
        
        # Usar updated_at si existe, sino created_at (para compatibilidad con registros antiguos)
        updated_at = fields.get("updated_at") or record.get("createdTime")
        
        return {
            "id": record.get("id"),
            "candidato": fields.get("candidato", []),
            "score_promedio": fields.get("score_promedio", 0),
            "score_admin": fields.get("score_admin", 0),
            "score_ops": fields.get("score_ops", 0),
            "score_biz": fields.get("score_biz", 0),
            "hands_on_index": fields.get("hands_on_index", 0),
            "potential_score": fields.get("potential_score", 0),
            "retention_risk": fields.get("retention_risk"),
            "profile_type": fields.get("profile_type"),
            "industry_tier": fields.get("industry_tier"),
            "risk_warning": fields.get("risk_warning"),
            "analysis_json": fields.get("analysis_json"),
            "created_at": record.get("createdTime"),
            "updated_at": updated_at  # Fecha de última actualización
        }
    
    # =========================================================================
    # Comentarios
    # =========================================================================
    
    async def get_comentarios(self, candidato_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene los comentarios de un candidato.
        Los comentarios se guardan como JSON en el campo 'notas' del candidato.
        """
        try:
            import json
            candidato = await self.get_candidato_by_id(candidato_id)
            if not candidato:
                return []
            
            notas_raw = candidato.get("notas", "")
            if not notas_raw:
                return []
            
            # Intentar parsear como JSON (lista de comentarios)
            try:
                comentarios = json.loads(notas_raw)
                if isinstance(comentarios, list):
                    return comentarios
            except json.JSONDecodeError:
                # Si no es JSON, crear un comentario con el texto plano
                return [{
                    "id": "legacy-1",
                    "autor": "Sistema",
                    "comentario": notas_raw,
                    "created_at": candidato.get("created_at", "")
                }]
            
            return []
        except Exception as e:
            print(f"[WARN] Error al obtener comentarios: {e}")
            return []
    
    async def create_comentario(
        self,
        candidato_id: str,
        autor: str,
        comentario: str
    ) -> Dict[str, Any]:
        """
        Crea un nuevo comentario.
        Los comentarios se guardan como JSON en el campo 'notas' del candidato.
        """
        import json
        from datetime import datetime
        import uuid
        
        try:
            # Obtener comentarios existentes
            comentarios_existentes = await self.get_comentarios(candidato_id)
            
            # Crear nuevo comentario
            nuevo_comentario = {
                "id": str(uuid.uuid4())[:8],
                "autor": autor,
                "comentario": comentario,
                "created_at": datetime.now().isoformat()
            }
            
            # Agregar al inicio de la lista
            comentarios_existentes.insert(0, nuevo_comentario)
            
            # Guardar como JSON en el campo notas
            notas_json = json.dumps(comentarios_existentes, ensure_ascii=False)
            
            await self.update_candidato(candidato_id, {"notas": notas_json})
            
            return nuevo_comentario
        except Exception as e:
            print(f"[ERROR] Error al crear comentario: {e}")
            raise
    
    def _format_comentario(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un registro de comentario."""
        if not record:
            return {}
        fields = record.get("fields", {})
        return {
            "id": record.get("id"),
            "autor": fields.get("autor_nombre"),
            "comentario": fields.get("comentario"),
            "created_at": record.get("createdTime")
        }
    
    # =========================================================================
    # Procesos
    # =========================================================================
    
    async def get_procesos(self, estado: Optional[str] = None, usuario_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene todos los procesos de reclutamiento con nombres resueltos."""
        filter_formula = None
        if estado and usuario_id:
            filter_formula = f"AND({{estado}} = '{estado}', FIND('{usuario_id}', ARRAYJOIN({{usuario_asignado}})))"
        elif estado:
            filter_formula = f"{{estado}} = '{estado}'"
        elif usuario_id:
            filter_formula = f"FIND('{usuario_id}', ARRAYJOIN({{usuario_asignado}}))"
        
        records = await self._get_records(
            self.config.table_procesos,
            filter_formula=filter_formula
        )
        
        # Resolver nombres de cargos y usuarios
        procesos = []
        for r in records:
            proceso = self._format_proceso_completo(r)
            
            # Si cargo_nombre es None, intentar resolver
            if not proceso.get("cargo_nombre") and proceso.get("cargo"):
                cargo_id = proceso["cargo"][0] if isinstance(proceso["cargo"], list) else proceso["cargo"]
                cargo = await self.get_cargo_by_id(cargo_id)
                if cargo:
                    proceso["cargo_nombre"] = cargo.get("nombre")
                    proceso["cargo_id"] = cargo_id
            
            # Si usuario_nombre es None, intentar resolver
            if not proceso.get("usuario_asignado_nombre") and proceso.get("usuario_asignado"):
                user_id = proceso["usuario_asignado"][0] if isinstance(proceso["usuario_asignado"], list) else proceso["usuario_asignado"]
                user = await self.get_usuario_by_id(user_id)
                if user:
                    proceso["usuario_asignado_nombre"] = user.get("nombre_completo")
                    proceso["usuario_asignado_id"] = user_id
            
            # Contar postulaciones vinculadas
            postulaciones = await self.get_candidatos(proceso_id=proceso["id"])
            proceso["postulaciones_count"] = len(postulaciones)
            
            procesos.append(proceso)
        
        return procesos
    
    async def get_proceso(self, codigo_proceso: str) -> Optional[Dict[str, Any]]:
        """Obtiene un proceso por su código."""
        record = await self._find_record_by_field(
            self.config.table_procesos,
            "codigo_proceso",
            codigo_proceso
        )
        return self._format_proceso(record) if record else None
    
    def _format_proceso(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un registro de proceso."""
        if not record:
            return {}
        fields = record.get("fields", {})
        return {
            "id": record.get("id"),
            "codigo_proceso": fields.get("codigo_proceso"),
            "cargo": fields.get("cargo", []),
            "estado": fields.get("estado"),
            "fecha_inicio": fields.get("fecha_inicio"),
            "fecha_cierre": fields.get("fecha_cierre"),
            "vacantes_proceso": fields.get("vacantes_proceso", 1),
            "notas": fields.get("notas"),
            "created_at": record.get("createdTime")
        }
    
    # =========================================================================
    # Configuración de Evaluación
    # =========================================================================
    
    async def get_active_config(self) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de evaluación activa."""
        filter_formula = "{is_active} = TRUE()"
        records = await self._get_records(
            self.config.table_config,
            filter_formula=filter_formula,
            max_records=1
        )
        return self._format_config(records[0]) if records else None
    
    async def create_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva configuración de evaluación."""
        fields = {
            "version": config_data.get("version", "1.0"),
            "nombre": config_data.get("nombre", "Default"),
            "is_active": config_data.get("is_active", False),
            "config_json": str(config_data),
        }
        record = await self._create_record(self.config.table_config, fields)
        return self._format_config(record)
    
    def _format_config(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un registro de configuración."""
        if not record:
            return {}
        fields = record.get("fields", {})
        return {
            "id": record.get("id"),
            "version": fields.get("version"),
            "nombre": fields.get("nombre"),
            "is_active": fields.get("is_active", False),
            "config_json": fields.get("config_json"),
            "created_at": record.get("createdTime")
        }
    
    # =========================================================================
    # Cargos
    # =========================================================================
    
    async def get_cargos(self, solo_activos: bool = True) -> List[Dict[str, Any]]:
        """Obtiene todos los cargos."""
        filter_formula = "{activo} = TRUE()" if solo_activos else None
        records = await self._get_records(
            self.config.table_cargos,
            filter_formula=filter_formula
        )
        return [self._format_cargo(r) for r in records]
    
    async def get_cargo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Obtiene un cargo por su código."""
        record = await self._find_record_by_field(
            self.config.table_cargos,
            "codigo",
            codigo
        )
        return self._format_cargo(record) if record else None
    
    def _format_cargo(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un registro de cargo."""
        if not record:
            return {}
        fields = record.get("fields", {})
        return {
            "id": record.get("id"),
            "codigo": fields.get("codigo"),
            "nombre": fields.get("nombre"),
            "descripcion": fields.get("descripcion"),
            "vacantes": fields.get("vacantes", 1),
            "activo": fields.get("activo", True),
            "created_at": record.get("createdTime")
        }
    
    async def get_cargo_by_id(self, cargo_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un cargo por su ID de Airtable."""
        url = f"{self._get_table_url(self.config.table_cargos)}/{cargo_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._format_cargo(response.json())
    
    # =========================================================================
    # Usuarios
    # =========================================================================
    
    async def get_usuarios(self) -> List[Dict[str, Any]]:
        """Obtiene todos los usuarios."""
        records = await self._get_records("Usuarios")
        return [self._format_usuario(r) for r in records]
    
    async def get_usuario_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtiene un usuario por email."""
        filter_formula = f"{{email}} = '{email}'"
        records = await self._get_records(
            "Usuarios",
            filter_formula=filter_formula,
            max_records=1
        )
        return self._format_usuario(records[0]) if records else None
    
    async def get_usuario_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un usuario por ID."""
        url = f"{self._get_table_url('Usuarios')}/{user_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._format_usuario(response.json())
    
    async def create_usuario(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo usuario."""
        fields = {
            "email": data["email"],
            "nombre_completo": data["nombre_completo"],
            "password_hash": data["password_hash"],
            "rol": data.get("rol", "usuario"),
            "activo": data.get("activo", True)
        }
        record = await self._create_record("Usuarios", fields)
        return self._format_usuario(record)
    
    async def update_usuario_last_login(self, user_id: str) -> None:
        """Actualiza el último login de un usuario."""
        from datetime import datetime
        fields = {"last_login": datetime.now().isoformat()}
        await self._update_record("Usuarios", user_id, fields)
    
    async def update_usuario_role(self, user_id: str, rol: str) -> None:
        """Actualiza el rol de un usuario."""
        await self._update_record("Usuarios", user_id, {"rol": rol})
    
    async def delete_usuario(self, user_id: str) -> bool:
        """Elimina un usuario."""
        return await self._delete_record("Usuarios", user_id)
    
    def _format_usuario(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un registro de usuario."""
        if not record:
            return {}
        fields = record.get("fields", {})
        return {
            "id": record.get("id"),
            "email": fields.get("email", ""),
            "nombre_completo": fields.get("nombre_completo", ""),
            "password_hash": fields.get("password_hash", ""),
            "rol": fields.get("rol", "usuario"),
            "activo": fields.get("activo", False),
            "last_login": fields.get("last_login"),
            "created_at": record.get("createdTime")
        }
    
    # =========================================================================
    # Procesos - Funciones adicionales
    # =========================================================================
    
    async def get_procesos_publicados(self) -> List[Dict[str, Any]]:
        """Obtiene procesos con estado 'publicado'."""
        filter_formula = "{estado} = 'publicado'"
        records = await self._get_records(
            self.config.table_procesos,
            filter_formula=filter_formula
        )
        return [self._format_proceso(r) for r in records]
    
    async def get_proceso_by_id(self, proceso_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un proceso por ID con nombres resueltos."""
        url = f"{self._get_table_url(self.config.table_procesos)}/{proceso_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            proceso = self._format_proceso_completo(response.json())
            
            # Resolver nombre del cargo
            if not proceso.get("cargo_nombre") and proceso.get("cargo"):
                cargo_id = proceso["cargo"][0] if isinstance(proceso["cargo"], list) else proceso["cargo"]
                cargo = await self.get_cargo_by_id(cargo_id)
                if cargo:
                    proceso["cargo_nombre"] = cargo.get("nombre")
                    proceso["cargo_id"] = cargo_id
            
            # Resolver nombre del usuario asignado
            if not proceso.get("usuario_asignado_nombre") and proceso.get("usuario_asignado"):
                user_id = proceso["usuario_asignado"][0] if isinstance(proceso["usuario_asignado"], list) else proceso["usuario_asignado"]
                user = await self.get_usuario_by_id(user_id)
                if user:
                    proceso["usuario_asignado_nombre"] = user.get("nombre_completo")
                    proceso["usuario_asignado_id"] = user_id
            
            # Contar postulaciones
            postulaciones = await self.get_candidatos(proceso_id=proceso_id)
            proceso["postulaciones_count"] = len(postulaciones)
            
            return proceso
    
    def _format_proceso_completo(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un registro de proceso con todos los campos."""
        if not record:
            return {}
        fields = record.get("fields", {})
        
        # Obtener nombre de cargo si existe el campo lookup
        cargo_nombre = None
        cargo_id = None
        if fields.get("cargo"):
            cargo_id = fields["cargo"][0] if isinstance(fields["cargo"], list) else fields["cargo"]
            # Si hay lookup de nombre
            cargo_nombre = fields.get("Nombre (from cargo)", [""])[0] if fields.get("Nombre (from cargo)") else None
        
        # Obtener nombre de usuario asignado
        usuario_nombre = None
        usuario_id = None
        if fields.get("usuario_asignado"):
            usuario_id = fields["usuario_asignado"][0] if isinstance(fields["usuario_asignado"], list) else fields["usuario_asignado"]
            usuario_nombre = fields.get("nombre_completo (from usuario_asignado)", [""])[0] if fields.get("nombre_completo (from usuario_asignado)") else None
        
        postulaciones = fields.get("Postulaciones", [])
        postulaciones_count = len(postulaciones) if isinstance(postulaciones, list) else 0
        
        return {
            "id": record.get("id"),
            "codigo_proceso": fields.get("codigo_proceso", ""),
            "cargo": fields.get("cargo", []),
            "cargo_id": cargo_id,
            "cargo_nombre": cargo_nombre,
            "usuario_asignado": fields.get("usuario_asignado", []),
            "usuario_asignado_id": usuario_id,
            "usuario_asignado_nombre": usuario_nombre,
            "estado": fields.get("estado", "publicado"),
            "vacantes_proceso": fields.get("vacantes_proceso", 1),
            "fecha_inicio": fields.get("fecha_inicio"),
            "fecha_cierre": fields.get("fecha_cierre"),
            "avances": fields.get("avances", ""),
            "bloqueos": fields.get("bloqueos", ""),
            "proximos_pasos": fields.get("proximos_pasos", ""),
            "notas": fields.get("notas", ""),
            "resultado": fields.get("resultado", ""),
            "postulaciones_count": postulaciones_count,
            "created_at": record.get("createdTime")
        }
    
    # =========================================================================
    # Procesos CRUD
    # =========================================================================
    
    async def create_proceso(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo proceso de reclutamiento."""
        fields = {
            "codigo_proceso": data["codigo_proceso"],
            "estado": data.get("estado", "publicado"),
            "vacantes_proceso": data.get("vacantes_proceso", 1),
        }
        
        if data.get("cargo"):
            fields["cargo"] = data["cargo"]
        if data.get("usuario_asignado"):
            fields["usuario_asignado"] = data["usuario_asignado"]
        if data.get("fecha_cierre"):
            fields["fecha_cierre"] = data["fecha_cierre"]
        if data.get("notas"):
            fields["notas"] = data["notas"]
        if data.get("fecha_inicio"):
            fields["fecha_inicio"] = data["fecha_inicio"]
        else:
            fields["fecha_inicio"] = datetime.now().strftime("%Y-%m-%d")
        
        record = await self._create_record(self.config.table_procesos, fields)
        return self._format_proceso_completo(record)
    
    async def update_proceso(self, proceso_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un proceso existente."""
        record = await self._update_record(self.config.table_procesos, proceso_id, data)
        return self._format_proceso_completo(record)
    
    # =========================================================================
    # Cargos CRUD
    # =========================================================================
    
    async def create_cargo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo cargo."""
        fields = {
            "codigo": data["codigo"],
            "nombre": data["nombre"],
            "descripcion": data.get("descripcion", ""),
            "vacantes": data.get("vacantes", 1),
            "activo": data.get("activo", True)
        }
        record = await self._create_record(self.config.table_cargos, fields)
        return self._format_cargo(record)
    
    async def update_cargo(self, cargo_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un cargo existente."""
        record = await self._update_record(self.config.table_cargos, cargo_id, data)
        return self._format_cargo(record)

